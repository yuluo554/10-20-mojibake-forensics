# recover/kun-jin-kao

状态：**M1 生成器已落地；M4 消费**。

- 构造：`EF BF BD`（U+FFFD）重复序列被 GBK 解码得到 `锟斤拷`。
- 期望：`LOST(reason="kun_jin_kao")` + 丢失点定位；输出不含自造字符。
