import sys
import tables
import numpy as np

fid = tables.open_file(sys.argv[1], 'a')

n_events = fid.root.index.shape[0]

zeros = np.zeros(n_events, np.uint16)
fid.create_array('/', 'classes', zeros)

zeros = np.zeros(n_events, np.uint8)
fid.create_array('/', 'matches', zeros)

zeros = np.zeros((1, 2), np.uint8)
fid.create_array('/', 'artifact_scores', zeros)

fid.close()
