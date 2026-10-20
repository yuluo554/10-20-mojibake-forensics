# file/zip-cjk-utf8

状态：**M1 生成器已落地；M5 消费**。

- 构造：zip 中文文件名，中央目录 `flag_bits & 0x800` 置位。
- 期望：按 UTF-8 解释；`zip_names` 输出该解释与证据。
