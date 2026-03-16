<template>
  <div class="header">
    <div class="header-left">
      <span :class="collapseBtnClass" style="cursor: pointer; font-size: 18px" @click="collapse"></span>
      <el-breadcrumb separator="/" style="display: inline-block; margin-left: 10px">
        <el-breadcrumb-item :to="'/'">首页</el-breadcrumb-item>
        <el-breadcrumb-item>{{ currentPathName }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <div class="header-user-con">
        <!-- 用户头像 -->
        <el-avatar class="user-avator" :size="30" :src="imgurl" />
        <!-- 用户名下拉菜单 -->
        <el-dropdown class="user-name">
          <div style="display: inline-block">
<!--            <img :src="user.avatarUrl" alt=""-->
<!--                 style="width: 30px; border-radius: 50%; position: relative; top: 10px; right: 5px">-->
            <span>{{ user.nickname }}</span>
            <i class="el-icon-arrow-down" style="margin-left: 5px"></i>
          </div>
          <!-- 用户名下拉菜单 -->
          <el-dropdown-menu slot="dropdown" style="width: 100px; text-align: center">
            <el-dropdown-item style="font-size: 14px; padding: 5px 0">
              <router-link to="/password">修改密码</router-link>
            </el-dropdown-item>
            <el-dropdown-item style="font-size: 14px; padding: 5px 0">
              <router-link to="/person">个人信息</router-link>
            </el-dropdown-item>
            <el-dropdown-item style="font-size: 14px; padding: 5px 0">
              <span style="text-decoration: none" @click="logout">退出</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Header",
  props: {
    collapseBtnClass: String,
    user: Object
  },
  computed: {
    currentPathName () {
      return this.$store.state.currentPathName;　　//需要监听的数据
    }
  },
  data() {
    return {
      imgurl: this.user.avatarUrl || '' // 初始化 imgurl
    }
  },
  methods: {
    collapse() {
      // this.$parent.$parent.$parent.$parent.collapse()  // 通过4个 $parent 找到父组件，从而调用其折叠方法
      this.$emit("asideCollapse")
    },
    logout() {
      this.$store.commit("logout")
      this.$message.success("退出成功")
    }
  },
  watch: {
    'user.avatarUrl': function(newVal) {
      this.imgurl = newVal;
    }
  }
}
</script>

<style scoped>
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-sizing: border-box;
    width: 100%;
    height: 70px;
  }

  .header-left {
    display: flex;
    align-items: center;
    padding-left: 20px;
    height: 100%;
  }
  .header-right {
    float: right;
    padding-right: 50px;
  }
  .header-user-con {
    display: flex;
    height: 70px;
    align-items: center;
  }

  .user-avator {
    margin: 0 10px 0 20px;
  }

</style>
