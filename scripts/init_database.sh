#!/bin/bash

echo "请输入 MySQL root 密码："
read -s ROOT_PASSWORD

mysql -u root -p"$ROOT_PASSWORD" << EOF
CREATE DATABASE IF NOT EXISTS tiktok_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'tiktok'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON tiktok_db.* TO 'tiktok'@'localhost';
FLUSH PRIVILEGES;

USE tiktok_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account VARCHAR(255) NOT NULL UNIQUE COMMENT '用户账号',
    track VARCHAR(100) NOT NULL COMMENT '对应赛道',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_account (account),
    INDEX idx_track (track)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
EOF

if [ $? -eq 0 ]; then
    echo "数据库初始化成功！"
    echo "连接信息："
    echo "  数据库: tiktok_db"
    echo "  用户: tiktok"
    echo "  密码: password"
else
    echo "数据库初始化失败，请检查 root 密码是否正确"
fi
