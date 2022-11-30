import pandas as pd
import xlsxwriter as xw
import csv,sys
from io import BytesIO
def edit_ebay_control_list(file_input):
    date = list(pd.read_csv(file_input, nrows=0).columns)[2]
    ebay_check_list = pd.read_csv(file_input, skiprows=1).fillna(0)
    ebay_check_list['mix'] = ebay_check_list['Palette_Box'].duplicated(keep= False).reset_index(drop= True)
    ebay_check_list['date'] = date
    rows = ebay_check_list.shape[0]+1
    columns = ebay_check_list.shape[1]
    # output = BytesIO()
    # workbook = xw.Workbook(output, {'in_memory': True})
    workbook = xw.Workbook('test.xlsx')
    worksheet = workbook.add_worksheet()

    for i in range(rows):
        for j in range(columns):
            if i == 0:
                worksheet.write(i,j,list(ebay_check_list.columns)[j])
                continue
            elif i<rows-1:
                mix = ebay_check_list.loc[ebay_check_list.index == i-1, 'mix']
                qty = ebay_check_list.loc[ebay_check_list.index == i-1, 'Qty_diff'].values[0]
                if mix.values[0] == True or qty > 1:
                    cell_format = {'bg_color':'red'}
                    cell_format_qty = {'bg_color':'red','font_size':14}
                    if j == 4:
                        worksheet.write(i,j, ebay_check_list.iloc[i-1,j], workbook.add_format(cell_format_qty))
                    else:
                        worksheet.write(i,j, ebay_check_list.iloc[i-1,j], workbook.add_format(cell_format))
                else:
                    worksheet.write(i,j, ebay_check_list.iloc[i-1,j])

    workbook.close()
    return date

date_output = edit_ebay_control_list(file_input= 'Outbound_packing_invoice.csv')
sys.exit()
date = list(pd.read_csv("Outbound_packing_invoice.csv", nrows=0).columns)[2]

ebay_check_list = pd.read_csv("Outbound_packing_invoice.csv", skiprows=1).fillna(0)
ebay_check_list['mix'] = ebay_check_list['Palette_Box'].duplicated(keep= False).reset_index(drop= True)
rows = ebay_check_list.shape[0]+1
columns = ebay_check_list.shape[1]

workbook = xw.Workbook('test.xlsx')
worksheet = workbook.add_worksheet()

for i in range(rows):
    for j in range(columns):
        if i == 0:
            worksheet.write(i,j,list(ebay_check_list.columns)[j])
            continue
        elif i<rows-1:
            mix = ebay_check_list.loc[ebay_check_list.index == i-1, 'mix']
            qty = ebay_check_list.loc[ebay_check_list.index == i-1, 'Qty_diff'].values[0]
            if mix.values[0] == True or qty > 1:
                cell_format = {'bg_color':'red'}
                cell_format_qty = {'bg_color':'red','font_size':14}
                if j == 4:
                    worksheet.write(i,j, ebay_check_list.iloc[i-1,j], workbook.add_format(cell_format_qty))
                else:
                    worksheet.write(i,j, ebay_check_list.iloc[i-1,j], workbook.add_format(cell_format))
            else:
                worksheet.write(i,j, ebay_check_list.iloc[i-1,j])

workbook.close()