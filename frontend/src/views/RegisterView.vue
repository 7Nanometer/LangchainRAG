<script setup>
/** 注册页 */
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register } from '@/api/auth'
import NanoLogo from '@/components/common/NanoLogo.vue'

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
        if (value && !/(?=.*[A-Za-z])(?=.*\d)/.test(value)) {
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
    <div class="auth-panel">
      <NanoLogo :size="28" :name-size="18" />
      <h1 class="auth-title">创建账号</h1>
      <p class="auth-sub">注册后即可提问，答案与回执将保存在你的账号下。</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        size="large"
        label-position="top"
        @keyup.enter="onSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="用户名（3~20 位）" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="密码（至少 8 位，含字母和数字）"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password placeholder="再输入一次密码" />
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
  padding: 32px 20px;
  background: var(--paper);
}
.auth-panel {
  width: 100%;
  max-width: 440px;
  border: 1px solid var(--rule);
  border-radius: var(--r-1);
  background: var(--panel);
  padding: 40px 40px 32px;
}
.auth-title {
  font-size: var(--fs-26);
  font-weight: 800;
  letter-spacing: -0.01em;
  margin: 22px 0 6px;
}
.auth-sub {
  font-size: var(--fs-13);
  color: var(--ink-2);
  margin: 0 0 26px;
  line-height: 1.75;
}
.submit-btn {
  width: 100%;
  margin-top: 4px;
}
.auth-footer {
  margin-top: 20px;
  font-size: var(--fs-13);
  color: var(--ink-3);
}
.auth-link {
  color: var(--ink);
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
}
@media (max-width: 840px) {
  .auth-panel {
    padding: 28px 24px 24px;
  }
}
</style>
