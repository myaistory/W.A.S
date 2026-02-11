import zipfile
import xml.etree.ElementTree as ET

def peek():
    try:
        with zipfile.ZipFile('/home/lianwei_zlw/Walnut-AI-Support/data/raw_tickets.xlsx', 'r') as z:
            # 读取 sharedStrings 来获取文本内容
            with z.open('xl/sharedStrings.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                # 提取前 20 条文本内容
                strings = [node.text for node in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if node.text]
                print('--- DATA_SAMPLES_START ---')
                for s in strings[:100]:
                    print(s)
                print('--- DATA_SAMPLES_END ---')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    peek()
