<template>
  <div class="register-container">
    <div class="register-box">
      <h1 class="title">用户注册</h1>
      <p class="subtitle">DSMS 缺陷检测管理系统</p>
      <el-form ref="formRef" :model="form" :rules="rules" class="register-form">
        <el-form-item prop="user_name">
          <el-input
            v-model="form.user_name"
            placeholder="用户名 (3-50字符)"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="real_name">
          <el-input
            v-model="form.real_name"
            placeholder="真实姓名 (1-50字符)"
            prefix-icon="UserFilled"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码 (8-128字符)"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="邮箱 (可选)"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="phone">
          <el-input
            v-model="form.phone"
            placeholder="电话 (可选)"
            prefix-icon="Phone"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="register-button"
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-link">
        <router-link to="/login">已有账号？立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const router = useRouter()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  user_name: '',
  real_name: '',
  password: '',
  confirmPassword: '',
  email: '',
  phone: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  user_name: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50字符', trigger: 'blur' }
  ],
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' },
    { min: 1, max: 50, message: '真实姓名长度为1-50字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度为8-128字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { max: 20, message: '电话最多20字符', trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await api.post('/auth/register', {
          user_name: form.user_name,
          real_name: form.real_name,
          password: form.password,
          email: form.email || undefined,
          phone: form.phone || undefined
        })
        ElMessage.success('注册成功，请登录')
        router.push('/login')
      } catch (error) {
        console.error('Register failed:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-box {
  width: 420px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.title {
  text-align: center;
  font-size: 28px;
  color: #333;
  margin-bottom: 8px;
}

.subtitle {
  text-align: center;
  font-size: 14px;
  color: #666;
  margin-bottom: 24px;
}

.register-form {
  margin-top: 16px;
}

.register-button {
  width: 100%;
}

.login-link {
  text-align: center;
  margin-top: 16px;
}

.login-link a {
  color: #667eea;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>
