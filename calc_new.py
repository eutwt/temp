"""
Payment History Profile (PHP) Calculator - Clean Version

This version leverages DuckDB's ability to reference previously defined columns
in the same SELECT statement to reduce CTEs and simplify the logic.
"""

import pandas as pd
import polars as pl
import duckdb
from datetime import datetime


def setup_database():
    """Initialize DuckDB connection with appropriate memory limit."""
    return duckdb.connect('temp.duckdb', config={'memory_limit': '30GB'})


def load_dates():
    """Load run date information from SAS dataset."""
    dates_df = pd.read_sas('data/dates.sas7bdat', encoding='latin1')
    run_date = dates_df.iloc[0][1]
    run_date_formatted = datetime.strptime(run_date, "%Y%m%d").strftime("%m%d%Y")
    return run_date, run_date_formatted


def load_reversal_data(run_date):
    """Load and prepare the main reversal data using Polars."""
    date_columns = [
        'rev_transaction_dt', 'otod', 'sor_dofd', 
        'trans_due_dt', 'rev_eff_date', 'pymt_tran_dt'
    ]
    
    pandas_df = pd.read_excel(f'data/sor_with_cx6_{run_date}.xlsx')
    pandas_df.columns = [col.lower() for col in pandas_df.columns]
    
    df = (
        pl.from_pandas(pandas_df)
        .with_columns([
            pl.col('account_status').cast(pl.Utf8),
            pl.col(pl.Datetime).cast(pl.Date),
            pl.col('rev_aftr_30_days').cast(pl.Boolean)
        ])
    )
    
    for col in date_columns:
        if col in df.columns:
            df = df.with_columns(
                pl.col(col).str.strptime(pl.Date, '%m/%d/%Y', strict=False)
            )
    
    return df


def calculate_php_periods(ddc):
    """Calculate PHP start and end periods for each loan."""
    return ddc.sql("""
        SELECT 
            ln_no,
            MIN(first_month) as start_month_php,
            MAX(rev_ss_month) as end_month_php
        FROM (
            SELECT 
                ln_no,
                Rev_Month_Snapshot,
                Rev_ss_month,
                Rev_Transaction_dt,
                MIN(pymt_ss_month) as first_month
            FROM sor_with_cx6
            GROUP BY ln_no, Rev_Month_Snapshot, Rev_ss_month, Rev_Transaction_dt
        )
        GROUP BY ln_no
    """)


def calculate_php_updates(ddc):
    """
    Main PHP calculation using DuckDB's column referencing capability.
    This combines all the logic into fewer, cleaner queries.
    """
    return ddc.sql("""
        SELECT 
            a.*,
            
            -- PHP period information
            b.start_month_php,
            b.end_month_php,
            
            -- Calculated fields using previously defined columns
            CASE 
                WHEN DAYOFMONTH(a.rev_month_snapshot) < 6
                THEN DATE_TRUNC('month', a.rev_month_snapshot - INTERVAL 1 MONTH)
                ELSE DATE_TRUNC('month', a.rev_month_snapshot)
            END as snapshot_month,
            
            -- Original 36-month PHP string
            CONCAT(a.pymt_hist_previous_2_yr, a.pymt_hist_previous_1_yr, a.pymt_hist_current_yr) as php_36_original,
            
            -- PHP start date calculation
            CASE 
                WHEN YEAR(a.otod) = 1899 
                THEN DATE_TRUNC('year', CURRENT_DATE) - INTERVAL 2 YEAR
                ELSE DATE_TRUNC('year', a.otod) - INTERVAL 2 YEAR
            END as php_start_date,
            
            -- Loan number formatting
            LPAD(CAST(a.ln_no AS VARCHAR), 10, '0') as loan_number_padded,
            
            -- Account status mapping
            CASE 
                WHEN account_status = '11' THEN '0'
                WHEN account_status = '71' THEN '1'
                WHEN account_status = '78' THEN '2'
                WHEN account_status = '80' THEN '3'
                WHEN account_status = '82' THEN '4'
                WHEN account_status = '83' THEN '5'
                WHEN account_status = '84' THEN '6'
            END as account_status_php_byte,
            
            -- Check for late reversals per loan
            MAX(a.rev_aftr_30_days) OVER (PARTITION BY a.ln_no) as has_late_reversal,
            
            -- Calculate update positions using previously defined columns
            GREATEST(1, DATEDIFF('month', php_start_date, start_month_php) + 1) as update_start_pos,
            LEAST(36, DATEDIFF('month', php_start_date, end_month_php) + 1) as update_end_pos,
            
            -- Position of current snapshot in PHP string
            CASE 
                WHEN snapshot_month BETWEEN start_month_php AND end_month_php
                THEN DATEDIFF('month', php_start_date, snapshot_month) + 1
                ELSE NULL
            END as snapshot_php_position,
            
            -- Build updated PHP string using string functions
            CASE
                -- If late reversal, mark all months in scope as 'D', preserving 'B' (bankruptcy)
                WHEN has_late_reversal THEN
                    CASE
                        WHEN update_start_pos > 1 AND update_end_pos < 36 THEN
                            SUBSTRING(php_36_original, 1, update_start_pos - 1) ||
                            REGEXP_REPLACE(
                                SUBSTRING(php_36_original, update_start_pos, update_end_pos - update_start_pos + 1),
                                '[^B]', 'D', 'g'
                            ) ||
                            SUBSTRING(php_36_original, update_end_pos + 1)
                        WHEN update_start_pos = 1 AND update_end_pos < 36 THEN
                            REGEXP_REPLACE(
                                SUBSTRING(php_36_original, 1, update_end_pos),
                                '[^B]', 'D', 'g'
                            ) ||
                            SUBSTRING(php_36_original, update_end_pos + 1)
                        WHEN update_start_pos > 1 AND update_end_pos = 36 THEN
                            SUBSTRING(php_36_original, 1, update_start_pos - 1) ||
                            REGEXP_REPLACE(
                                SUBSTRING(php_36_original, update_start_pos),
                                '[^B]', 'D', 'g'
                            )
                        ELSE
                            REGEXP_REPLACE(php_36_original, '[^B]', 'D', 'g')
                    END
                
                -- If no late reversal, update specific snapshot positions with account status
                WHEN NOT has_late_reversal AND snapshot_php_position IS NOT NULL AND account_status_php_byte IS NOT NULL THEN
                    CASE
                        WHEN snapshot_php_position = 1 THEN
                            account_status_php_byte || SUBSTRING(php_36_original, 2)
                        WHEN snapshot_php_position = 36 THEN
                            SUBSTRING(php_36_original, 1, 35) || account_status_php_byte
                        ELSE
                            SUBSTRING(php_36_original, 1, snapshot_php_position - 1) ||
                            account_status_php_byte ||
                            SUBSTRING(php_36_original, snapshot_php_position + 1)
                    END
                    
                -- Otherwise keep original
                ELSE php_36_original
            END as php_36_updated,
            
            -- Split updated PHP into yearly segments using the updated string
            SUBSTRING(php_36_updated, 1, 12) as new_previous_2_yr,
            SUBSTRING(php_36_updated, 13, 12) as new_previous_1_yr,
            SUBSTRING(php_36_updated, 25, 12) as new_current_yr,
            
            -- Update indicators using the new yearly segments
            CASE WHEN new_previous_2_yr <> a.pymt_hist_previous_2_yr THEN 'Y' ELSE 'N' END as update_prev_2_yr,
            CASE WHEN new_previous_1_yr <> a.pymt_hist_previous_1_yr THEN 'Y' ELSE 'N' END as update_prev_1_yr,
            CASE WHEN new_current_yr <> a.pymt_hist_current_yr THEN 'Y' ELSE 'N' END as update_current_yr
            
        FROM sor_with_cx6 a
        LEFT JOIN calculate_php_periods b ON a.ln_no = b.ln_no
    """)


def calculate_cx6_updates(ddc):
    """Calculate CX6 PHP updates in a single query."""
    return ddc.sql("""
        SELECT 
            a.ln_no,
            a.payment_history_profile,
            a.file_date,
            b.start_month_php as payment_date,
            
            -- Calculate months between payment and file date
            DATEDIFF('month', payment_date, a.file_date) as months_between,
            
            -- CX6 PHP update logic using the months_between calculation
            CASE
                WHEN a.payment_history_profile IS NULL THEN NULL
                WHEN months_between <= 1 THEN a.payment_history_profile
                ELSE 
                    REGEXP_REPLACE(
                        SUBSTRING(a.payment_history_profile, 1, months_between - 1),
                        '[123456JKL0]', 'D', 'g'
                    ) ||
                    SUBSTRING(a.payment_history_profile, months_between)
            END as cx6_php_updated,
            
            -- Special handling for accurate status (no late reversals)
            CASE 
                WHEN NOT a.has_late_reversal 
                     AND a.payment_history_profile IS NOT NULL
                     AND a.rev_month_snapshot <= DATE_TRUNC('month', CURRENT_DATE) + INTERVAL 5 DAY
                     AND LEFT(a.payment_history_profile, 1) <> 'B'
                THEN a.account_status_php_byte || SUBSTRING(a.payment_history_profile, 2)
                ELSE NULL
            END as cx6_accurate_php_updated
            
        FROM calculate_php_updates a
        LEFT JOIN calculate_php_periods b ON a.ln_no = b.ln_no
    """)


def generate_final_output(ddc):
    """Generate the final output report."""
    return ddc.sql("""
        SELECT 
            -- Account identifiers
            CONCAT('51', a.loan_number_padded) as "CX6 Account Number",
            STRFTIME(a.pymt_tran_dt, '%m/%d/%Y') as "PMT_TRANSACTION_DT",
            STRFTIME(a.rev_month_snapshot, '%m/%d/%Y') as "Impacted_Snapshot",
            
            -- Account status information
            a.account_status as "Account Status",
            CASE WHEN a.payment_history_profile IS NOT NULL THEN a.account_status ELSE '' END as "What Account Status Should be In Current File",
            
            -- Account status update indicator
            CASE 
                WHEN a.payment_history_profile IS NULL THEN ''
                WHEN a.rev_month_snapshot >= DATE_TRUNC('month', a.rev_transaction_dt) + INTERVAL 5 DAY
                     AND a.cx6_account_status <> a.account_status 
                THEN 'Y' 
                ELSE 'N' 
            END as "Account Status Update Indicator",
            
            a.cx6_account_status as "account_sts_CX6",
            
            -- CX6 PHP information
            COALESCE(b.cx6_accurate_php_updated, b.cx6_php_updated) as "What CX6 PHP string should be",
            a.payment_history_profile,
            
            -- CX6 PHP update indicator using the coalesced value
            CASE 
                WHEN a.payment_history_profile IS NULL THEN ''
                WHEN a.payment_history_profile <> "What CX6 PHP string should be" THEN 'Y'
                ELSE 'N' 
            END as "CX6 PHP String Update Indicator",
            
            -- Overall CX6 update indicator
            CASE 
                WHEN "Account Status Update Indicator" = 'Y' OR "CX6 PHP String Update Indicator" = 'Y'
                THEN 'Y' ELSE 'N'
            END as "CX6_Update_Indicator",
            
            -- AFS PHP strings and indicators
            a.pymt_hist_current_yr as "AFS Current Year String",
            a.new_current_yr as "Updated AFS Current Year String",
            a.update_current_yr as "AFS Current Year PHP String Update Indicator",
            
            a.pymt_hist_previous_1_yr as "AFS Previous 1 Year String",
            a.new_previous_1_yr as "Updated AFS Previous 1 Year String",
            a.update_prev_1_yr as "AFS Previous 1 Year PHP String Update Indicator",
            
            -- DOFD information
            STRFTIME(a.sor_dofd, '%m/%d/%Y') as "L_CB_1ST_DLQ_DATE",
            CASE
                WHEN a.sor_dofd IS NOT NULL
                     AND YEAR(a.sor_dofd) <> 1899
                     AND (a.account_status = '11' OR a.rev_aftr_30_days)
                THEN 'Y' ELSE 'N' 
            END as "DOFD Update Indicator",
            
            -- Update strings for processing
            CASE 
                WHEN a.update_current_yr = 'Y'
                THEN CONCAT(a.loan_number_padded, '////', a.pymt_hist_current_yr, '/', a.new_current_yr)
                ELSE NULL 
            END as "Current Year Update",
            
            CASE 
                WHEN a.update_prev_1_yr = 'Y'
                THEN CONCAT(a.loan_number_padded, '////', a.pymt_hist_previous_1_yr, '/', a.new_previous_1_yr)
                ELSE NULL 
            END as "Previous 1 Year Update",
            
            CASE 
                WHEN a.sor_dofd IS NOT NULL AND YEAR(a.sor_dofd) <> 1899 AND a.account_status = '11'
                THEN CONCAT(a.loan_number_padded, '////', STRFTIME(a.sor_dofd, '%m%d%y'), '/', '0')
            END as "DOFD Update",
            
            -- Manual review indicator
            CASE 
                WHEN a.has_df_tran = 'Yes' AND a.has_due_date_change = 'No' AND a.pymt_hist_current_yr IS NOT NULL
                     AND (a.date_closed IS NULL OR a.date_closed >= DATE_TRUNC('month', a.rev_transaction_dt))
                THEN 'Y - Deferral'
                
                WHEN a.has_df_tran = 'No' AND a.has_due_date_change = 'Yes' AND a.pymt_hist_current_yr IS NOT NULL
                     AND (a.date_closed IS NULL OR a.date_closed >= DATE_TRUNC('month', a.rev_transaction_dt))
                THEN 'Y - Due Date'
                
                WHEN a.has_df_tran = 'No' AND a.has_due_date_change = 'No' AND a.pymt_hist_current_yr IS NULL
                     AND (a.date_closed IS NULL OR a.date_closed >= DATE_TRUNC('month', a.rev_transaction_dt))
                THEN 'Y - SOR PHP'
                
                WHEN a.has_df_tran = 'No' AND a.has_due_date_change = 'No' AND a.pymt_hist_current_yr IS NOT NULL
                     AND a.date_closed IS NOT NULL AND a.date_closed < DATE_TRUNC('month', a.rev_transaction_dt)
                THEN 'Y - Date Closed'
                
                WHEN a.has_df_tran = 'No' AND a.has_due_date_change = 'No' AND a.pymt_hist_current_yr IS NOT NULL
                     AND (a.date_closed IS NULL OR a.date_closed >= DATE_TRUNC('month', a.rev_transaction_dt))
                THEN 'N'
                
                ELSE 'Y - Multi' 
            END as "Requires_Manual_Review"
            
        FROM calculate_php_updates a
        LEFT JOIN calculate_cx6_updates b ON a.ln_no = b.ln_no
    """)


def main():
    """Main execution function."""
    print("Starting clean PHP calculation process...")
    
    # Setup
    ddc = setup_database()
    run_date, run_date_formatted = load_dates()
    print(f"Processing data for run date: {run_date}")
    
    # Load data
    print("Loading reversal data...")
    reversal_data = load_reversal_data(run_date)
    ddc.register("sor_with_cx6", reversal_data.to_pandas())
    
    # Register views in order
    print("Calculating PHP periods...")
    ddc.register("calculate_php_periods", calculate_php_periods(ddc))
    
    print("Calculating PHP updates...")
    ddc.register("calculate_php_updates", calculate_php_updates(ddc))
    
    print("Calculating CX6 updates...")
    ddc.register("calculate_cx6_updates", calculate_cx6_updates(ddc))
    
    # Generate final output
    print("Generating final output...")
    output_df = generate_final_output(ddc).df()
    
    # Create Excel report
    print("Creating Excel report...")
    report_label = pd.DataFrame({
        'report_label': ['Wells Fargo Confidential, Not for Remediation.']
    })
    
    output_filename = f'data/AFS_Pymt_Rev_GoFrwd_{run_date_formatted}_clean.xlsx'
    with pd.ExcelWriter(output_filename) as writer:
        output_df.to_excel(writer, sheet_name='Reversals', index=False)
        report_label.to_excel(writer, sheet_name='report_label', index=False)
    
    print(f"Report saved to: {output_filename}")
    print("Clean PHP calculation completed successfully!")
