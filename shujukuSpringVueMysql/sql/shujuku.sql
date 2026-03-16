/*
 Navicat Premium Data Transfer

 Source Server         : start
 Source Server Type    : MySQL
 Source Server Version : 80032
 Source Host           : localhost:3306
 Source Schema         : cl_dcs

 Target Server Type    : MySQL
 Target Server Version : 80032
 File Encoding         : 65001

 Date: 16/03/2026 20:31:31
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for dish
-- ----------------------------
DROP TABLE IF EXISTS `dish`;
CREATE TABLE `dish`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '课程名称',
  `score` int NULL DEFAULT NULL COMMENT '学分',
  `times` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '上课时间',
  `state` tinyint(1) NULL DEFAULT NULL COMMENT '是否开课',
  `grader_id` int NULL DEFAULT NULL COMMENT '授课老师id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of dish
-- ----------------------------
INSERT INTO `dish` VALUES (1, '麻婆豆腐', 10, '40', 0, 4);
INSERT INTO `dish` VALUES (2, '香煎土豆', 20, '45', 1, 5);
INSERT INTO `dish` VALUES (3, 'French fries', 30, '30', 1, 6);
INSERT INTO `dish` VALUES (4, 'Yu-Shiang Eggplant', 50, '60', NULL, 4);
INSERT INTO `dish` VALUES (5, '炒豆芽', 12, '12', NULL, 18);

-- ----------------------------
-- Table structure for owner_dish
-- ----------------------------
DROP TABLE IF EXISTS `owner_dish`;
CREATE TABLE `owner_dish`  (
  `owner_id` int NOT NULL COMMENT '用户ID',
  `dish_id` int NOT NULL COMMENT '菜品ID',
  PRIMARY KEY (`owner_id`, `dish_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of owner_dish
-- ----------------------------
INSERT INTO `owner_dish` VALUES (1, 1);
INSERT INTO `owner_dish` VALUES (1, 2);
INSERT INTO `owner_dish` VALUES (1, 3);
INSERT INTO `owner_dish` VALUES (4, 1);
INSERT INTO `owner_dish` VALUES (4, 3);
INSERT INTO `owner_dish` VALUES (16, 1);
INSERT INTO `owner_dish` VALUES (16, 2);
INSERT INTO `owner_dish` VALUES (16, 3);
INSERT INTO `owner_dish` VALUES (18, 1);
INSERT INTO `owner_dish` VALUES (18, 2);
INSERT INTO `owner_dish` VALUES (18, 3);
INSERT INTO `owner_dish` VALUES (18, 4);
INSERT INTO `owner_dish` VALUES (21, 1);
INSERT INTO `owner_dish` VALUES (21, 2);
INSERT INTO `owner_dish` VALUES (28, 1);
INSERT INTO `owner_dish` VALUES (28, 2);
INSERT INTO `owner_dish` VALUES (34, 1);
INSERT INTO `owner_dish` VALUES (34, 2);
INSERT INTO `owner_dish` VALUES (34, 3);

-- ----------------------------
-- Table structure for sys_dict
-- ----------------------------
DROP TABLE IF EXISTS `sys_dict`;
CREATE TABLE `sys_dict`  (
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '名称',
  `value` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '内容',
  `type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '类型'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_dict
-- ----------------------------
INSERT INTO `sys_dict` VALUES ('user', 'el-icon-user', 'icon');
INSERT INTO `sys_dict` VALUES ('house', 'el-icon-house', 'icon');
INSERT INTO `sys_dict` VALUES ('menu', 'el-icon-menu', 'icon');
INSERT INTO `sys_dict` VALUES ('s-custom', 'el-icon-s-custom', 'icon');
INSERT INTO `sys_dict` VALUES ('s-grid', 'el-icon-s-grid', 'icon');
INSERT INTO `sys_dict` VALUES ('document', 'el-icon-document', 'icon');
INSERT INTO `sys_dict` VALUES ('coffee', 'el-icon-coffee\r\n', 'icon');
INSERT INTO `sys_dict` VALUES ('s-marketing', 'el-icon-s-marketing', 'icon');

-- ----------------------------
-- Table structure for sys_menu
-- ----------------------------
DROP TABLE IF EXISTS `sys_menu`;
CREATE TABLE `sys_menu`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '菜单ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '名称',
  `path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '路径',
  `icon` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '图标',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '描述',
  `pid` int NULL DEFAULT NULL COMMENT '父级ID',
  `page_path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '页面路径',
  `sort_num` int NULL DEFAULT NULL COMMENT '排序',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 63 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '菜单表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_menu
-- ----------------------------
INSERT INTO `sys_menu` VALUES (4, '系统管理', NULL, 'el-icon-s-grid', NULL, NULL, NULL, 1);
INSERT INTO `sys_menu` VALUES (5, '用户管理', '/user', 'el-icon-user', NULL, 4, 'User', 101);
INSERT INTO `sys_menu` VALUES (6, '角色管理', '/role', 'el-icon-s-custom', NULL, 4, 'Role', 102);
INSERT INTO `sys_menu` VALUES (7, '菜单管理', '/menu', 'el-icon-menu', NULL, 4, 'Menu', 103);
INSERT INTO `sys_menu` VALUES (10, '主页面', '/home', 'el-icon-house', NULL, NULL, 'Home', 0);
INSERT INTO `sys_menu` VALUES (44, '信息管理', '', 'el-icon-document', NULL, NULL, '', 10);
INSERT INTO `sys_menu` VALUES (55, '菜品统计', '/orderstats', 'el-icon-user', NULL, 54, 'OrderStats', 100);

-- ----------------------------
-- Table structure for sys_role
-- ----------------------------
DROP TABLE IF EXISTS `sys_role`;
CREATE TABLE `sys_role`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '名称',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '描述',
  `flag` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_role
-- ----------------------------
INSERT INTO `sys_role` VALUES (1, '管理员', '管理员', 'ROLE_ADMIN');
INSERT INTO `sys_role` VALUES (2, '用户', '用户', 'ROLE_OWNERS');
INSERT INTO `sys_role` VALUES (3, '厨师', '厨师', 'ROLE_DISH');

-- ----------------------------
-- Table structure for sys_role_menu
-- ----------------------------
DROP TABLE IF EXISTS `sys_role_menu`;
CREATE TABLE `sys_role_menu`  (
  `role_id` int NOT NULL COMMENT '角色id',
  `menu_id` int NOT NULL COMMENT '菜单id',
  PRIMARY KEY (`role_id`, `menu_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '角色菜单关系表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_role_menu
-- ----------------------------
INSERT INTO `sys_role_menu` VALUES (1, 4);
INSERT INTO `sys_role_menu` VALUES (1, 5);
INSERT INTO `sys_role_menu` VALUES (1, 6);
INSERT INTO `sys_role_menu` VALUES (1, 7);
INSERT INTO `sys_role_menu` VALUES (1, 10);
INSERT INTO `sys_role_menu` VALUES (1, 39);
INSERT INTO `sys_role_menu` VALUES (1, 44);
INSERT INTO `sys_role_menu` VALUES (1, 46);
INSERT INTO `sys_role_menu` VALUES (2, 10);
INSERT INTO `sys_role_menu` VALUES (2, 39);
INSERT INTO `sys_role_menu` VALUES (2, 44);
INSERT INTO `sys_role_menu` VALUES (2, 46);
INSERT INTO `sys_role_menu` VALUES (3, 10);
INSERT INTO `sys_role_menu` VALUES (3, 39);
INSERT INTO `sys_role_menu` VALUES (3, 44);
INSERT INTO `sys_role_menu` VALUES (3, 46);

-- ----------------------------
-- Table structure for sys_user
-- ----------------------------
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `password` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码',
  `nickname` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '昵称',
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '电话',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '地址',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `avatar_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '头像',
  `role` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 22 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_user
-- ----------------------------
INSERT INTO `sys_user` VALUES (1, 'admin', '21232f297a57a5a743894a0e4a801fc3', '管理员', 'admin@qq.com', '15698745685', '北京', '2022-01-22 21:10:27', 'http://localhost:9090/file/3d9349ddacd8479ca693f18f4a0d6db5.png', 'ROLE_ADMIN');
INSERT INTO `sys_user` VALUES (2, 'yong1', '202cb962ac59075b964b07152d234b70', 'yong1', 'john.doee@example.com', NULL, NULL, '2025-05-13 09:50:16', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (3, 'yong2', '202cb962ac59075b964b07152d234b70', 'yong2', 'jane.smith@example.com', NULL, NULL, '2025-05-13 09:51:18', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (4, 'chu1', '202cb962ac59075b964b07152d234b70', 'chu1', 'michael.johnson@example.com', NULL, NULL, '2025-05-13 09:57:30', NULL, 'ROLE_DISH');
INSERT INTO `sys_user` VALUES (5, 'chu2', '202cb962ac59075b964b07152d234b70', 'chu2', 'emily.williams@example.com', NULL, NULL, '2025-05-13 09:57:55', NULL, 'ROLE_DISH');
INSERT INTO `sys_user` VALUES (6, 'yong3', '202cb962ac59075b964b07152d234b70', 'yong3', 'david.brown@example.com', NULL, NULL, '2025-05-13 09:58:23', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (7, 'yong4', '202cb962ac59075b964b07152d234b70', 'yong4', 'sarah.miller@example.com', NULL, NULL, '2025-05-13 09:58:45', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (8, 'aaa', '202cb962ac59075b964b07152d234b70', 'chu3', NULL, NULL, NULL, '2025-05-13 09:59:06', NULL, 'ROLE_DISH');
INSERT INTO `sys_user` VALUES (9, 'sss', '202cb962ac59075b964b07152d234b70', 'chu4', 'chris.jones@example.com', NULL, NULL, '2025-05-13 09:59:16', NULL, 'ROLE_DISH');
INSERT INTO `sys_user` VALUES (10, 'ddd', '202cb962ac59075b964b07152d234b70', 'yong5', NULL, NULL, NULL, '2025-05-13 09:59:32', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (11, 'fff', '202cb962ac59075b964b07152d234b70', 'chu5', NULL, NULL, NULL, '2025-05-13 09:59:43', NULL, 'ROLE_DISH');
INSERT INTO `sys_user` VALUES (12, 'ggg', '202cb962ac59075b964b07152d234b70', '一号', NULL, NULL, NULL, '2025-05-13 10:03:05', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (14, '哈哈哈', '202cb962ac59075b964b07152d234b70', '二号', NULL, NULL, NULL, '2025-05-13 10:41:05', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (15, 'yong5', '202cb962ac59075b964b07152d234b70', NULL, NULL, NULL, NULL, '2025-05-13 10:52:22', NULL, 'ROLE_DISH');
INSERT INTO `sys_user` VALUES (16, 'yong6', '202cb962ac59075b964b07152d234b70', NULL, NULL, NULL, NULL, '2025-05-13 11:02:25', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (17, 'yong10', '202cb962ac59075b964b07152d234b70', NULL, NULL, NULL, NULL, '2025-05-13 11:11:51', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (18, 'yong78', '202cb962ac59075b964b07152d234b70', 'yong78', NULL, NULL, NULL, '2025-05-13 11:40:06', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (19, 'yong89', '202cb962ac59075b964b07152d234b70', NULL, NULL, NULL, NULL, '2025-05-13 11:40:30', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (20, 'yong15', '202cb962ac59075b964b07152d234b70', NULL, NULL, NULL, NULL, '2025-05-13 12:28:53', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (21, 'yong99', 'e8f80f215c4f258ec211fcd7f266a1de', 'yong99', 'john.doeeE@example.com', NULL, NULL, '2025-05-14 12:24:48', NULL, 'ROLE_OWNERS');
INSERT INTO `sys_user` VALUES (22, 'yong74', '202cb962ac59075b964b07152d234b70', 'yong74', NULL, NULL, NULL, '2025-05-14 14:04:34', NULL, 'ROLE_OWNERS');

SET FOREIGN_KEY_CHECKS = 1;
