# node
物理节点，就是一台机器，节点内部可以有多个GPU(一台机器有多卡)

# rank & local_rank
用于表示进程的序号，用于进程间通信。每一个进程对应了一个rank

rank=0的进程就是master进程

local_rank： rank是指在整个分布式任务中进程的序号；local_rank是指在一台机器上(一个node上)进程的相对序号，例如机器一上有0,1,2,3,4,5,6,7，机器二上也有0,1,2,3,4,5,6,7。local_rank在node之间相互独立

单机多卡时，rank就等于local_rank

# nnodes
物理节点数量

# node_rank
物理节点的序号

# nproc_per_node
每个物理节点上面进程的数量

# group

进程组。默认只有一个组

# world size 全局的并行数
全局（一个分布式任务）中，rank的数量

每个node包含16个GPU，且nproc_per_node=8，nnodes=3，机器的node_rank=5，请问world_size是多少？ 答案：world_size = 3*8 = 24
