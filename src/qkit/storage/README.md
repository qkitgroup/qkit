## Sample code
How to open a file that you have in your storage database.

```python
import qkit
qkit.start()

from qkit.storage import Data
path = qkit.store_db.get('UUID') # you can also specify the *absolute* path tho your .h5 file directly

df = Data(path)
amplitudes = df.data.amplitude[:] #if you data is in /data0/amplitude
```

Please note that the `storage_db` has nothing to do with the contents in this folder. The db is created in `qkit.core.lib.file_service.file_tools.store_db`.

If you pass a non-absolute filename to `Data()`, the file will be created in your data folder.
