# RQAMSClient

[RQAMS](https://www.ricequant.com/welcome/ams) 是由米筐科技开发的，集多资产管理、实时监控、绩效分析、风险分析等多种功能于一体的智能投资组合管理平台。

RQAMSClient 为管理 RQAMS 平台上的资源（交割单、组合、产品等）提供了 Python 接口，大幅提升了 RQAMS 的自动化程度，打通了量化交易和资管系统。

***项目处于开发阶段，测试尚不完善，请谨慎用于生产环境。***

***支持 Python 3.6+***

## 安装

```shell script
pip install rqams-client
```

## 示例

```python
>>> from rqams_client import RQAMSClient
>>> client = RQAMSClient(username="cuizi7@163.com", password="xxxxxx")
>>> client.asset_units
{5de71b12ed4803a654d486c8: AssetUnit(id=5de71b12ed4803a654d486c8, name=接口测试), 5ddfa7a81366d9db63f81286: AssetUnit(id=5ddfa7a81366d9db63f81286, name=测试期权), 5db147ab3e1305c4be6fbd3f: AssetUnit(id=5db147ab3e1305c4be6fbd3f, name=公募), 5d9065c9e4c91056df7c027e: AssetUnit(id=5d9065c9e4c91056df7c027e, name=均价测试), 5d8defe7f792ca44dc04c9b6: AssetUnit(id=5d8defe7f792ca44dc04c9b6, name=弘论-自动对账资产单元)}
>>>
```


## API 文档

TODO
