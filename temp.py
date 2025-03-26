import zipfile
import xml.etree.ElementTree as ET
import random
import shutil
import os
from pathlib import Path

def sample_excel_rows(input_file, output_file, sample_size, sheet_index=0):
    """
    Sample rows from an Excel file by directly manipulating the XML.
    
    Args:
        input_file: Path to the input Excel file
        output_file: Path to save the sampled Excel file
        sample_size: Number of rows to sample (excluding header)
        sheet_index: Index of the sheet to sample from (0-based)
    """
    # Create a temporary directory
    temp_dir = Path("temp_excel_extract")
    temp_dir.mkdir(exist_ok=True)
    
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
        zip_ref.extract(sheet_path, temp_dir)
    
    # Parse the sheet XML
    sheet_xml_path = temp_dir / sheet_path
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
    
    # Clean up
    shutil.rmtree(temp_dir)
    
    return output_file

# Example usage
if __name__ == "__main__":
    input_file = "original.xlsx"
    output_file = "sampled.xlsx"
    sample_excel_rows(input_file, output_file, sample_size=100)
    print(f"Sampled Excel file saved to {output_file}")
