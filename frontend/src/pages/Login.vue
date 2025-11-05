<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="logo">
          <el-icon :size="48" color="var(--safeline-primary)"><Lock /></el-icon>
        </div>
        <h1>Telegram 客服系统</h1>
        <p>SafeLine 防护版</p>
      </div>

      <el-card class="login-card">
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          label-position="top"
          size="large"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
              clearable
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item>
            <el-checkbox v-model="loginForm.remember">记住密码</el-checkbox>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              style="width: 100%"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <el-link type="primary" :underline="false">忘记密码？</el-link>
          <el-divider direction="vertical" />
          <el-link type="primary" :underline="false">注册账号</el-link>
        </div>
      </el-card>

      <div class="page-footer">
        <span>© 2025 Telegram Customer Service System</span>
        <el-divider direction="vertical" />
        <span>Powered by SafeLine</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const router = useRouter()
const loginFormRef = ref()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为 3-20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()

    loading.value = true

    const { data } = await axios.post(`${API_BASE}/api/auth/login`, {
      username: loginForm.username,
      password: loginForm.password
    })

    // 保存 token
    localStorage.setItem('access_token', data.access_token)

    if (loginForm.remember) {
      localStorage.setItem('username', loginForm.username)
    }

    ElMessage.success('登录成功！')

    // 跳转到工作台
    router.push('/workbench')
  } catch (error: any) {
    if (error.response) {
      ElMessage.error(error.response.data.detail || '登录失败')
    } else if (error.errors) {
      // 表单验证错误
      return
    } else {
      ElMessage.error('登录失败，请检查网络连接')
    }
  } finally {
    loading.value = false
  }
}

// 从本地存储加载用户名
const savedUsername = localStorage.getItem('username')
if (savedUsername) {
  loginForm.username = savedUsername
  loginForm.remember = true
}
</script>

<style scoped lang="scss">
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;

  .login-container {
    width: 100%;
    max-width: 400px;

    .login-header {
      text-align: center;
      margin-bottom: 32px;

      .logo {
        margin-bottom: 16px;
        display: flex;
        justify-content: center;

        .el-icon {
          padding: 20px;
          background: white;
          border-radius: 50%;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
      }

      h1 {
        color: white;
        font-size: 28px;
        font-weight: 700;
        margin: 0 0 8px 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
      }

      p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 14px;
        margin: 0;
      }
    }

    .login-card {
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);

      :deep(.el-card__body) {
        padding: 32px;
      }

      .login-footer {
        text-align: center;
        margin-top: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
      }
    }

    .page-footer {
      text-align: center;
      margin-top: 24px;
      color: rgba(255, 255, 255, 0.8);
      font-size: 13px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;

      :deep(.el-divider--vertical) {
        background-color: rgba(255, 255, 255, 0.3);
        height: 14px;
      }
    }
  }
}
</style>
