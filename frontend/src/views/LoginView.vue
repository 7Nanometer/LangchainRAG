<script setup>
/** 登录页 */
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { login } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    const data = await login({ username: form.username.trim(), password: form.password })
    userStore.setLogin(data.token, data.user)
    ElMessage.success(`欢迎回来，${data.user.username}`)
    // 登录前想去哪个页面，登录后送回哪里；没记录就去聊天页
    router.push(route.query.redirect ? String(route.query.redirect) : '/chat')
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
      <div class="auth-brand">💬 知识库智能问答</div>
      <div class="auth-sub">电商商品知识库 · 有问必答 · 答案附出处</div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        size="large"
        label-position="top"
        @keyup.enter="onSubmit"
      >
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="密码"
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
          登 录
        </el-button>
      </el-form>

      <div class="auth-footer">
        还没有账号？
        <router-link class="auth-link" to="/register">立即注册</router-link>
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
