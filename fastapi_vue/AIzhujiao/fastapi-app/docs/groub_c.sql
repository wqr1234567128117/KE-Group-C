/*
 Navicat Premium Dump SQL

 Source Server         : 知识工程C
 Source Server Type    : MySQL
 Source Server Version : 80028 (8.0.28)
 Source Host           : 39.107.241.146:3306
 Source Schema         : groub_c

 Target Server Type    : MySQL
 Target Server Version : 80028 (8.0.28)
 File Encoding         : 65001

 Date: 07/04/2026 14:04:45
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for chat_records
-- ----------------------------
DROP TABLE IF EXISTS `chat_records`;
CREATE TABLE `chat_records`  (
  `record_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `session_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `qa_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `question_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `answer_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `knowledge_source` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `image_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `asked_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`record_id`) USING BTREE,
  INDEX `fk_chat_records_user`(`user_id` ASC) USING BTREE,
  CONSTRAINT `fk_chat_records_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of chat_records
-- ----------------------------

-- ----------------------------
-- Table structure for homework_assists
-- ----------------------------
DROP TABLE IF EXISTS `homework_assists`;
CREATE TABLE `homework_assists`  (
  `assist_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `assist_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `submitted_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `correction_suggestion` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `solving_hint` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `submitted_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`assist_id`) USING BTREE,
  INDEX `fk_homework_assists_user`(`user_id` ASC) USING BTREE,
  CONSTRAINT `fk_homework_assists_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of homework_assists
-- ----------------------------

-- ----------------------------
-- Table structure for learning_paths
-- ----------------------------
DROP TABLE IF EXISTS `learning_paths`;
CREATE TABLE `learning_paths`  (
  `path_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `estimated_days` int NULL DEFAULT NULL,
  `status` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `current_task_point` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `updated_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`path_id`) USING BTREE,
  INDEX `fk_learning_paths_user`(`user_id` ASC) USING BTREE,
  CONSTRAINT `fk_learning_paths_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of learning_paths
-- ----------------------------

-- ----------------------------
-- Table structure for learning_progress
-- ----------------------------
DROP TABLE IF EXISTS `learning_progress`;
CREATE TABLE `learning_progress`  (
  `progress_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `path_id` int NULL DEFAULT NULL,
  `task_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `related_task_id` int NULL DEFAULT NULL,
  `study_minutes` int NULL DEFAULT NULL,
  `record_time` datetime NULL DEFAULT NULL,
  `progress_note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`progress_id`) USING BTREE,
  INDEX `fk_learning_progress_user`(`user_id` ASC) USING BTREE,
  CONSTRAINT `fk_learning_progress_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of learning_progress
-- ----------------------------

-- ----------------------------
-- Table structure for path_tasks
-- ----------------------------
DROP TABLE IF EXISTS `path_tasks`;
CREATE TABLE `path_tasks`  (
  `task_id` int NOT NULL AUTO_INCREMENT,
  `path_id` int NOT NULL,
  `task_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `task_description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `task_order` int NULL DEFAULT NULL,
  `is_completed` tinyint NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `updated_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`task_id`) USING BTREE,
  INDEX `fk_path_tasks_path`(`path_id` ASC) USING BTREE,
  CONSTRAINT `fk_path_tasks_path` FOREIGN KEY (`path_id`) REFERENCES `learning_paths` (`path_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of path_tasks
-- ----------------------------

-- ----------------------------
-- Table structure for task_questions
-- ----------------------------
DROP TABLE IF EXISTS `task_questions`;
CREATE TABLE `task_questions`  (
  `question_id` int NOT NULL AUTO_INCREMENT,
  `task_id` int NOT NULL,
  `question_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `correct_answer` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `is_passed` tinyint NULL DEFAULT NULL,
  `user_answer` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `updated_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`question_id`) USING BTREE,
  INDEX `fk_task_questions_task`(`task_id` ASC) USING BTREE,
  CONSTRAINT `fk_task_questions_task` FOREIGN KEY (`task_id`) REFERENCES `path_tasks` (`task_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of task_questions
-- ----------------------------

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `major` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `updated_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`user_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
