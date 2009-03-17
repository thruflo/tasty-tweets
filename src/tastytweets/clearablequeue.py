import os
import shutil

from directory_queue.directory_queue import DirectoryQueue


class ClearableDirectoryQueue(DirectoryQueue):
    
    def clearDone(self):
        dirlist = os.listdir(self.queues['done'])
        for item in dirlist:
            item_path = os.path.join(self.queues['done'], item)
            shutil.rmtree(item_path)
        
    
    def clearError(self):
        dirlist = os.listdir(self.queues['error'])
        for item in dirlist:
            item_path = os.path.join(self.queues['error'], item)
            shutil.rmtree(item_path)
        
    
    
    def clear(self):
        self.clearDone()
        self.clearError()
    

