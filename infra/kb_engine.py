import json

class WalnutKB:
    def __init__(self, kb_path):
        self.kb_path = kb_path
        with open(kb_path, 'r', encoding='utf-8') as f:
            self.kb_data = json.load(f)

    def search(self, query):
        query = query.lower()
        results = []
        for key, entry in self.kb_data.items():
            score = sum(1 for kw in entry['keywords'] if kw in query)
            if score > 0:
                results.append((score, entry['answer']))
        
        if not results: return None
        # 返回匹配分数最高的答案
        results.sort(key=lambda x: x[0], reverse=True)
        return results[0][1]

kb_engine = WalnutKB('/home/lianwei_zlw/Walnut-AI-Support/data/walnut_kb.json')
