<template>
  <div class="login-bg">
    <div class="login-container">
      <div class="login-header">
        <img class="logo mr10" src="../assets/logo.svg" alt="" />
        <div class="login-title">智能助教系统</div>
      </div>
      <el-form :model="user" :rules="rules" ref="userForm" size="large">
        <el-form-item prop="username">
          <el-input size="medium" prefix-icon="el-icon-user" v-model="user.username" placeholder="用户名"></el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input size="medium"
                    prefix-icon="el-icon-lock"
                    show-password
                    v-model="user.password"
                    placeholder="密码">
          </el-input>
        </el-form-item>
        <el-form-item style="margin: 10px 0; text-align: right">
          <p class="login-tips">Tips : 用户名和密码在user表。</p>
          <el-button class="login-btn" type="primary" size="large" autocomplete="off" @click="login">登录</el-button>
          <p class="login-text">
            没有账号？<el-link type="primary" @click="$router.push('/register')">立即注册</el-link>
          </p>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import {setRoutes} from "@/router";

export default {
  name: "Login",
  data() {
    return {
      user: {},
      rules: {
        username: [
          {required: true, message: '请输入用户名', trigger: 'blur'},
          {min: 3, max: 10, message: '长度在 3 到 5 个字符', trigger: 'blur'}
        ],
        password: [
          {required: true, message: '请输入密码', trigger: 'blur'},
          {min: 1, max: 20, message: '长度在 1 到 20 个字符', trigger: 'blur'}
        ],
      }
    }
  },
  methods: {
    login() {
      this.$refs['userForm'].validate((valid) => {
        if (valid) {  // 表单校验合法
          this.request.post("/user/login", this.user).then(res => {
            if (res.code === '200') {
              localStorage.setItem("user", JSON.stringify(res.data))  // 存储用户信息到浏览器
              localStorage.setItem("menus", JSON.stringify(res.data.menus))  // 存储用户信息到浏览器
              // 动态设置当前用户的路由
              setRoutes()
              this.$message.success("登录成功")

              if (res.data.role === 'ROLE_OWNERS') {
                this.$router.push("/")
              } else {
                this.$router.push("/")
              }
            } else {
              this.$message.error(res.msg)
            }
          })
        }
      });
    }
  }
}
</script>

<style scoped>
.login-bg {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100vh;
  background: url(../assets/login-bg1.png) center/cover no-repeat;
}

.login-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40px;
}

.logo {
  width: 35px;
}

.login-title {
  font-size: 22px;
  color: #333;
  font-weight: bold;
}

.login-container {
  width: 450px;
  border-radius: 5px;
  background: #fff;
  padding: 40px 50px 50px;
  box-sizing: border-box;
}

.pwd-tips {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  margin: -10px 0 10px;
  color: #787878;
}

.pwd-checkbox {
  height: auto;
}

.login-btn {
  display: block;
  width: 100%;
}

.login-tips {
  font-size: 12px;
  color: #999;
}

.login-text {
  display: flex;
  align-items: center;
  margin-top: 20px;
  font-size: 14px;
  color: #787878;
}
</style>
