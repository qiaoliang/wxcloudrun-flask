  1. localrun_improved.sh
   - 自动检测并生成缺失的迁移脚本
   - 适用于首次部署或迁移脚本丢失的情况

  2. localrun_complete.sh
   - 包含所有 localrun_improved.sh 的功能
   - 额外支持 --reset-db 选项，可以完全重置数据库
   - 使用方法：
   1   # 正常启动
   2   ./localrun_complete.sh
   3
   4   # 重置数据库并启动
   5   ./localrun_complete.sh --reset-db

  关键改进：

   1. 自动化迁移脚本生成：解决了没有迁移脚本时启动失败的问题
   2. 清晰的日志输出：每个步骤都有明确的成功/失败提示
   3. 数据库重置选项：方便开发时快速清理环境
   4. 正确的约束：新生成的数据库不会对 phone_number 有 UNIQUE 约束

  使用建议：

   - 首次部署：使用 ./localrun_complete.sh
   - 日常开发：如果遇到数据库问题，使用 ./localrun_complete.sh --reset-db
   - 生产环境：确保手动备份后再使用 --reset-db 选项

