# 查询NPU网卡对接设备信息（对端要使能LLDP）
## 单网卡查询LLDP全量信息
hccn_tool -i 0 -lldp -g  
## 单网卡查询LLDP关键信息（仅显示对端接口、IP地址及设备名称）
hccn_tool -i 0 -lldp -g | sed -n '/Ifname/p;/IPv4/p;/System Name TLV/{n;p}'|awk '{sub(/^[\t ]*/,"");print}'
## 批量查询LLDP关键信息（仅显示对端接口、IP地址及设备名称）
for i in $(seq 0 7); do echo "======NPU_$i======";hccn_tool -i $i -lldp -g | sed -n '/Ifname/p;/IPv4/p;/System Name TLV/{n;p}'|awk '{sub(/^[\t ]*/,"");print}';done


# 批量查询NPU网口状态
for i in $(seq 0 7); do echo "NPU_$i:"; hccn_tool -i $i -link -g;done

# 配置NPU网卡IP地址 
hccn_tool -i 0 -ip -s address 177.1.1.1 netmask 255.255.255.0

# 批量配置Node_NPU IP地址
hccn_tool -i 0 -ip -s address x.x.x.2 netmask 255.255.255.0
hccn_tool -i 1 -ip -s address x.x.x.3 netmask 255.255.255.0
hccn_tool -i 2 -ip -s address x.x.x.4 netmask 255.255.255.0
hccn_tool -i 3 -ip -s address x.x.x.5 netmask 255.255.255.0
hccn_tool -i 4 -ip -s address x.x.x.6 netmask 255.255.255.0
hccn_tool -i 5 -ip -s address x.x.x.7 netmask 255.255.255.0
hccn_tool -i 6 -ip -s address x.x.x.8 netmask 255.255.255.0
hccn_tool -i 7 -ip -s address x.x.x.9 netmask 255.255.255.0

# 批量查询NPU网卡IP地址
for i in $(seq 0 7); do echo "NPU_$i:"; hccn_tool -i $i -ip -g;done


# 批量配置NPU网关
for i in {0..7};do hccn_tool -i $i -gateway -s gateway x.x.x+1.1;done
for i in {0..7};do hccn_tool -i $i -gateway -g;done

# 批量配置网络检测对象
for i in {0..7};do hccn_tool -i $i -netdetect -s address x.x.x+1.1;done

# 批量PING网关
for i in {0..7};do hccn_tool -i $i -ping -g address x.x.x+1.1;done

# PING对端NPU IP
hccn_tool -i 0 -ping -g address x.x.x+1.2

# 查看NPU网卡光模块状态查询
hccn_tool -i 0 -optical -g

# 批量查询NPU网口速率
for i in $(seq 0 7); do echo "NPU_$i:"; hccn_tool -i $i -speed -g;done

# NPU网卡切速 （特定情况下NPU200G与交换机100G互通时，需将NPU网卡切速到100G）
hccn_tool -i 0 -generic -s static_speed 100000

# NPU网口自适应切速（默认开启自动切速auto_adapt；当NPU网卡切速后，可配置自适应切速恢复）
hccn_tool -i 0 -generic -s auto_adapt

# 查看NPU网卡配置文件；若修改NPU网卡hccn.conf配置文件，需要重新加载配置文件
cat /etc/hccn.conf

# 修改hccn.conf配置文件前，建议先本地保存原始数据
cp /etc/hccn.conf /etc/hccn.conf.backup

## 单网卡恢复配置文件
hccn_tool -i 0 -cfg recovery
## 批量恢复配置文件
for i in $(seq 0 7); do echo "NPU_$i:"; hccn_tool -i $i -cfg recovery;done