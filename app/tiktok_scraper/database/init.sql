CREATE DATABASE IF NOT EXISTS tiktok_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE tiktok_db;

CREATE TABLE IF NOT EXISTS tracks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '赛道名称',
    description VARCHAR(500) NULL COMMENT '赛道描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='赛道表';

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account VARCHAR(255) NOT NULL UNIQUE COMMENT '用户账号',
    track_id INT NOT NULL COMMENT '赛道ID',
    url VARCHAR(500) NULL COMMENT '完整链接',
    sec_user_id VARCHAR(255) NULL COMMENT 'Sec User ID',
    region VARCHAR(100) NULL COMMENT '地区',
    tags JSON NULL COMMENT '标签',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_account (account),
    INDEX idx_track_id (track_id),
    CONSTRAINT fk_user_track FOREIGN KEY (track_id) REFERENCES tracks(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

CREATE TABLE IF NOT EXISTS user_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(500) NOT NULL COMMENT '用户URL',
    username VARCHAR(255) NULL COMMENT '用户名',
    following VARCHAR(50) NULL COMMENT '关注数',
    followers VARCHAR(50) NULL COMMENT '粉丝数',
    likes VARCHAR(50) NULL COMMENT '点赞数',
    video_count VARCHAR(50) NULL COMMENT '视频数',
    videos JSON NULL COMMENT '视频信息',
    user_info JSON NULL COMMENT '用户详细信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    INDEX idx_url (url),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户历史记录表';

