# 通过官方镜像拉起容器
```sh
IMAGE=vllm-ascend:xxxx
NAME=xx

docker run -itd \
    --name ${NAME} --privileged --net=host -w /home/ \
    --device /dev/davinci0 --device /dev/davinci1 --device /dev/davinci2 --device /dev/davinci3 \
    --device /dev/davinci4 --device /dev/davinci5 --device /dev/davinci6 --device /dev/davinci7 \
    --device /dev/davinci8 --device /dev/davinci9 --device /dev/davinci10 --device /dev/davinci11 \
    --device /dev/davinci12 --device /dev/davinci13 --device /dev/davinci14 --device /dev/davinci15 \
    --device /dev/davinci_manager --device /dev/devmm_svm --device /dev/hisi_hdc \
    -v /usr/local/dcmi:/usr/local/dcmi -v /usr/local/sbin/npu-smi:/usr/local/sbin/npu-smi \
    -v /usr/local/Ascend/driver/:/usr/local/Ascend/driver/ \
    -v /etc/ascend_install.info:/etc/ascend_install.info -v /home:/home -v /data:/data\
    --shm-size=128g ${IMAGE}

echo "start container:{$NAME} success!"
```