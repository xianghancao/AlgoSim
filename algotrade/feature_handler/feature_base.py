
class FeatureBase():
    def __init__(self, store_path):
        self.store_path = store_path
        
        
    def gen_feature(self, dataObj): 
        pass
        
    def _store(self):
        return