# golang安装

```sh
wget https://mirrors.aliyun.com/golang/go1.23.8.linux-arm64.tar.gz
tar -C /usr/local -xzf go1.23.8.linux-arm64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
# 然后执行 go version可以看到版本即安装成功
```

# 新项目依赖安装

一般一个go项目下会有go.mod文件，里面记录了这个项目依赖的包

```sh
# 在go.mod所在目录下执行
go mod tidy
```

### golang 源配置

如果下载golang package遇到了报错 Gateway Time-out
可以通过配置直接访问github解决（需要服务器上配代理，确保稳定访问github）：

```sh
go env -w GOSUMDB=off   # 不验证CA证书
go env -w GOPROXY=direct  # 直接访问github拉取
```