<template>
  <div style="color: #666;font-size: 14px;">
    <div style="padding-bottom: 20px">
      <b>欢迎你！{{ user.nickname }}</b>
    </div>
    <el-card>
      欢迎登入智能助教系统！
    </el-card>
    <div style="height: 1px; background: #ddd; margin: 20px 0"/>

    <el-row :gutter="30">
      <el-col :span="12">
        <div style="padding: 20px 0; font-size: 20px">技术</div>
        <el-row>
          <el-col :span="12" style="line-height: 30px">
            <div><b>模型使用</b></div>
            <div>模型</div>
          </el-col>
          <el-col :span="12" style="line-height: 30px">
            <b>数据集</b>
            <div>基于xxx</div>
          </el-col>
        </el-row>
      </el-col>
    </el-row>

  </div>
</template>

<script>
export default {
  name: "Home",
  data() {
    return {
      user: localStorage.getItem("user") ? JSON.parse(localStorage.getItem("user")) : {}
    }
  }
}
</script>
