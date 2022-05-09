from multiprocessing import Queue
import select



que = Queue()
# que.put(1)
(rr, wr, err) = select.select([que._reader],[],[], 0.1)

# print(rr[0].recv())
print(rr, wr, err)