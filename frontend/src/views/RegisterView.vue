<script setup>
/** 注册页 */
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { register } from '@/api/auth'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '', confirm: '' })

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3~20 位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value && !(/(?=.*[A-Za-z])(?=.*\d)/.test(value))) {
          callback(new Error('密码必须同时包含字母和数字，例如 demo12345'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  confirm: [
    { required: true, message: '请再输入一次密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function onSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    await register({ username: form.username.trim(), password: form.password })
    ElMessage.success('注册成功，请登录')
    router.push({ path: '/login', query: { username: form.username.trim() } })
  } catch {
    /* 错误提示已由 request.js 统一弹出 */
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">创建账号</div>
      <div class="auth-sub">注册后即可向商品知识库提问</div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        size="large"
        label-position="top"
        @keyup.enter="onSubmit"
      >
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名（3~20 位）" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="密码（至少 8 位，含字母和数字）"
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-form-item prop="confirm">
          <el-input
            v-model="form.confirm"
            type="password"
            show-password
            placeholder="再输入一次密码"
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="submit-btn"
          :loading="loading"
          @click="onSubmit"
        >
          注 册
        </el-button>
      </el-form>

      <div class="auth-footer">
        已有账号？
        <router-link class="auth-link" to="/login">去登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(1200px 500px at 20% -10%, rgba(37, 99, 235, 0.18), transparent),
    radial-gradient(900px 500px at 110% 110%, rgba(16, 185, 129, 0.14), transparent),
    var(--app-bg);
}
.auth-card {
  width: 100%;
  max-width: 400px;
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 40px 36px 28px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.08);
}
.auth-brand {
  font-size: 22px;
  font-weight: 700;
  text-align: center;
}
.auth-sub {
  margin: 8px 0 28px;
  text-align: center;
  font-size: 13px;
  color: var(--text-second);
}
.submit-btn {
  width: 100%;
  margin-top: 4px;
}
.auth-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 13px;
  color: var(--text-second);
}
.auth-link {
  color: var(--brand);
  text-decoration: none;
}
</style>
