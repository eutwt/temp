import zipfile
import xml.etree.ElementTree as ET
import random
import shutil
import os
from pathlib import Path
import pandas as pd
import tempfile

def sample_excel_rows(input_file, output_file, sample_size, sheet_index=0):
    """
    Sample rows from an Excel file by directly manipulating the XML for XLSX files
    or using pandas for XLS files.
    
    Args:
        input_file: Path to the input Excel file
        output_file: Path to save the sampled Excel file
        sample_size: Number of rows to sample (excluding header)
        sheet_index: Index of the sheet to sample from (0-based)
    """
    # Check file extension
    file_ext = Path(input_file).suffix.lower()
    
    if file_ext == '.xlsx':
        # For XLSX files, use the XML approach
        return sample_xlsx_rows(input_file, output_file, sample_size, sheet_index)
    elif file_ext == '.xls':
        # For XLS files, use a different approach since they're not ZIP archives
        return sample_xls_rows(input_file, output_file, sample_size, sheet_index)
    else:
        raise ValueError(f"Unsupported file extension: {file_ext}. Only .xlsx and .xls are supported.")

def sample_xlsx_rows(input_file, output_file, sample_size, sheet_index=0):
    """
    Sample rows from an XLSX file by directly manipulating the XML.
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Copy the original file to avoid modifying it
        shutil.copy(input_file, output_file)
        
        # Extract the sheet XML
        with zipfile.ZipFile(output_file, 'r') as zip_ref:
            # Find the sheet XML file
            sheet_files = [f for f in zip_ref.namelist() if f.startswith('xl/worksheets/sheet')]
            if not sheet_files or sheet_index >= len(sheet_files):
                raise ValueError(f"Sheet index {sheet_index} not found")
            
            sheet_path = sheet_files[sheet_index]
            
            # Extract the sheet XML
            zip_ref.extract(sheet_path, temp_dir_path)
        
        # Parse the sheet XML
        sheet_xml_path = temp_dir_path / sheet_path
        tree = ET.parse(sheet_xml_path)
        root = tree.getroot()
        
        # Find all rows
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        rows = root.findall('.//s:row', ns)
        
        if len(rows) <= 1:
            raise ValueError("Not enough rows to sample")
        
        # Keep the header row (first row)
        header_row = rows[0]
        
        # Sample from the remaining rows
        data_rows = rows[1:]
        if sample_size >= len(data_rows):
            print(f"Warning: Requested sample size {sample_size} is >= available rows {len(data_rows)}")
            sampled_rows = data_rows
        else:
            sampled_rows = random.sample(data_rows, sample_size)
        
        # Sort the sampled rows by row index to maintain order
        sampled_rows.sort(key=lambda r: int(r.get('r')))
        
        # Remove all rows from the XML
        for row in rows:
            parent = root.find('./s:sheetData', ns)
            if parent is not None:
                parent.remove(row)
        
        # Add back the header and sampled rows
        sheet_data = root.find('./s:sheetData', ns)
        sheet_data.append(header_row)
        
        # Update row indices to be sequential
        for i, row in enumerate(sampled_rows):
            row.set('r', str(i + 2))  # +2 because header is row 1
            # Update cell references
            for cell in row.findall('.//s:c', ns):
                old_ref = cell.get('r')
                if old_ref:
                    # Extract column letter part
                    col = ''.join(c for c in old_ref if c.isalpha())
                    cell.set('r', f"{col}{i + 2}")
            
            sheet_data.append(row)
        
        # Save the modified XML
        tree.write(sheet_xml_path)
        
        # Update the zip file with the modified sheet
        with zipfile.ZipFile(output_file, 'a') as zip_ref:
            zip_ref.write(sheet_xml_path, sheet_path)
    
    return output_file

def sample_xls_rows(input_file, output_file, sample_size, sheet_index=0):
    """
    Sample rows from an XLS file using pandas and xlwt.
    
    Note: This approach doesn't preserve all formatting but maintains data types.
    For XLS files, we need to use a different library since they're not ZIP archives.
    """
    try:
        import xlrd
        import xlwt
        from xlutils.copy import copy as xl_copy
    except ImportError:
        raise ImportError("Please install xlrd, xlwt, and xlutils: pip install xlrd xlwt xlutils")
    
    # Open the workbook
    rb = xlrd.open_workbook(input_file, formatting_info=True)
    
    # Check if sheet index is valid
    if sheet_index >= rb.nsheets:
        raise ValueError(f"Sheet index {sheet_index} not found")
    
    # Get the sheet
    sheet = rb.sheet_by_index(sheet_index)
    
    # Check if there are enough rows
    if sheet.nrows <= 1:
        raise ValueError("Not enough rows to sample")
    
    # Create a copy of the workbook
    wb = xl_copy(rb)
    
    # Get the sheet to modify
    out_sheet = wb.get_sheet(sheet_index)
    
    # Sample row indices (excluding header)
    if sample_size >= sheet.nrows - 1:
        print(f"Warning: Requested sample size {sample_size} is >= available rows {sheet.nrows - 1}")
        sampled_indices = list(range(1, sheet.nrows))
    else:
        sampled_indices = sorted(random.sample(range(1, sheet.nrows), sample_size))
    
    # Create a new workbook
    new_wb = xlwt.Workbook()
    
    # Copy all sheets from the original workbook
    for sheet_idx in range(rb.nsheets):
        sheet = rb.sheet_by_index(sheet_idx)
        new_sheet = new_wb.add_sheet(sheet.name)
        
        # If this is the sheet we're sampling
        if sheet_idx == sheet_index:
            # Copy header row
            for col in range(sheet.ncols):
                new_sheet.write(0, col, sheet.cell_value(0, col))
            
            # Copy sampled rows
            for i, row_idx in enumerate(sampled_indices):
                for col in range(sheet.ncols):
                    new_sheet.write(i + 1, col, sheet.cell_value(row_idx, col))
        else:
            # Copy entire sheet
            for row in range(sheet.nrows):
                for col in range(sheet.ncols):
                    new_sheet.write(row, col, sheet.cell_value(row, col))
    
    # Save the new workbook
    new_wb.save(output_file)
    
    return output_file

# Example usage
if __name__ == "__main__":
    input_file = "data.xlsx"  # or "data.xls"
    output_file = "sampled_data" + Path(input_file).suffix
    sample_excel_rows(input_file, output_file, sample_size=100)
    print(f"Sampled Excel file saved to {output_file}")
