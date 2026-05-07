<template>
  <div class="login-container">
    <div class="login-box">
      <h1 class="title">DSMS</h1>
      <p class="subtitle">缺陷检测管理系统</p>
      <el-form ref="formRef" :model="form" :rules="rules" class="login-form">
        <el-form-item prop="user_name">
          <el-input
            v-model="form.user_name"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-link">
        <router-link to="/register">还没有账号？立即注册</router-link>
      </div>
      <div class="demo-link">
        <router-link to="/demo">体验演示</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  user_name: '',
  password: ''
})

const rules = {
  user_name: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await authStore.login(form.user_name, form.password)
        ElMessage.success('登录成功')
        router.push('/dashboard')
      } catch (error) {
        console.error('Login failed:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.title {
  text-align: center;
  font-size: 32px;
  color: #333;
  margin-bottom: 8px;
}

.subtitle {
  text-align: center;
  font-size: 14px;
  color: #666;
  margin-bottom: 32px;
}

.login-form {
  margin-top: 24px;
}

.login-button {
  width: 100%;
}

.register-link {
  text-align: center;
  margin-top: 16px;
}

.register-link a {
  color: #667eea;
  text-decoration: none;
}

.register-link a:hover {
  text-decoration: underline;
}

.demo-link {
  text-align: center;
  margin-top: 10px;
}

.demo-link a {
  color: #10b981;
  text-decoration: none;
  font-size: 14px;
}

.demo-link a:hover {
  text-decoration: underline;
}
</style>
