from connect import *

users = '''CREATE TABLE IF NOT EXISTS `users` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT, 
    `user_id` BIGINT NOT NULL,  
    `full_name` VARCHAR(256) NOT NULL,
    `admin` TINYINT NOT NULL
);'''
cursor.execute(users)

groups = '''CREATE TABLE IF NOT EXISTS `groups` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `chat_id` BIGINT NOT NULL,
    `title` VARCHAR(256) NOT NULL,
    `username` VARCHAR(64),
    `admins` TEXT,
    `add_quantity` BIGINT
);'''
cursor.execute(groups)

allowed_members = '''CREATE TABLE IF NOT EXISTS `allowed_members` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `chat_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL
);'''
cursor.execute(allowed_members)

added_members = '''CREATE TABLE IF NOT EXISTS `added_members` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `chat_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `full_name` TEXT NOT NULL,
    `quantity` BIGINT NOT NULL,
    `required_members` BIGINT NOT NULL
);'''
cursor.execute(added_members)

groups = '''CREATE TABLE IF NOT EXISTS `top` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `chat_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `full_name` VARCHAR(256) NOT NULL,
    `added_members_count` VARCHAR(256) NOT NULL
);'''
cursor.execute(groups)


groups = '''CREATE TABLE IF NOT EXISTS `delete_messages` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `chat_id` BIGINT NOT NULL,
    `message_id` BIGINT NOT NULL,
    `delete_time` BIGINT NOT NULL
);'''
cursor.execute(groups)

mailing = '''CREATE TABLE IF NOT EXISTS `mailing` (
    `message_id` BIGINT NULL,
    `from_user_id` BIGINT NULL,
    `reply_markup` TEXT,
    `last_user_id` BIGINT NULL,
    `mail_type` TINYTEXT,
    `status` TINYINT
);'''
cursor.execute(mailing)

users_blacklist = '''CREATE TABLE IF NOT EXISTS `users_blacklist` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `full_name` VARCHAR(255) NOT NULL,
    CONSTRAINT `UNIQUE USER` UNIQUE (`user_id`)
)'''
cursor.execute(users_blacklist)

groups_blacklist = '''CREATE TABLE IF NOT EXISTS `groups_blacklist` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `group_id` BIGINT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    CONSTRAINT `UNIQUE USER` UNIQUE (`group_id`)
)'''
cursor.execute(groups_blacklist)