<script setup>
/** 登录页：左侧登录表单 + 右侧"示例回执"（一看就懂系统在做什么） */
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'
import { useUserStore } from '@/stores/user'
import NanoLogo from '@/components/common/NanoLogo.vue'

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
    <div class="auth-panel">
      <!-- 左：登录表单 -->
      <div class="auth-col auth-form-col">
        <NanoLogo :size="28" :name-size="18" />
        <h1 class="auth-title">登录</h1>
        <p class="auth-sub">登录后向商品知识库提问，每条回答都附一张可核对回执。</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          size="large"
          label-position="top"
          @keyup.enter="onSubmit"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
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
        <div class="auth-demo num">演示账号 demo ／ 密码 demo12345</div>
      </div>

      <!-- 右：示例回执（示意数据，演示"回答长什么样"） -->
      <div class="auth-col auth-specimen-col">
        <div class="specimen">
          <div class="specimen-head">
            <span class="u-label">示例回执</span>
            <span class="specimen-note">示意数据 · 登录后可见真实回执</span>
          </div>

          <div class="specimen-answer">
            可以的，W1 耳机支持防汗，运动时佩戴没问题。防水等级为 <b>IPX5</b>，可防汗、防小雨<span class="cite-mark">1</span><span class="cite-mark">2</span>。
          </div>

          <div class="specimen-receipt">
            <span class="sr-mark" />
            <span class="sr-label">回执</span>
            <span class="sr-id num">№1024</span>
            <span class="sr-dim num">2 段来源</span>
            <span class="sr-dim">相关度 <span class="num">78%</span></span>
            <span class="sr-time num">14:32</span>
          </div>
          <div class="specimen-rows">
            <div class="specimen-row">
              <span class="sr-idx num">[1]</span>
              <span class="sr-file">商品资料-无线耳机W1.md</span>
              <span class="sr-score"><i class="score-block s1" /><span class="num">78%</span></span>
            </div>
            <div class="specimen-row">
              <span class="sr-idx num">[2]</span>
              <span class="sr-file">售后政策与常见问题.txt</span>
              <span class="sr-score"><i class="score-block s3" /><span class="num">64%</span></span>
            </div>
            <div class="specimen-meta num">
              检索：向量 20 段 ＋ 关键词 12 段 → 融合 26 段 → 采纳 2 段（阈值 0.52） · 生成耗时 1.9 秒
            </div>
          </div>
        </div>
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
  max-width: 880px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  border: 1px solid var(--rule);
  border-radius: var(--r-1);
  background: var(--panel);
}
.auth-col {
  padding: 40px 40px 32px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.auth-specimen-col {
  border-left: 1px solid var(--rule);
  background: var(--paper-2);
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
.auth-demo {
  margin-top: 8px;
  font-size: var(--fs-11);
  color: var(--ink-3);
  letter-spacing: 0.03em;
}

/* ---- 示例回执 ---- */
.specimen {
  border: 1px solid var(--rule);
  border-radius: var(--r-1);
  background: var(--panel);
  padding: 18px 18px 14px;
}
.specimen-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 14px;
}
.specimen-note {
  font-size: var(--fs-11);
  color: var(--ink-3);
}
.specimen-answer {
  font-size: var(--fs-13);
  line-height: 1.8;
  color: var(--ink);
  margin-bottom: 14px;
}
.cite-mark {
  display: inline-block;
  min-width: 14px;
  height: 14px;
  line-height: 14px;
  text-align: center;
  font-size: 9.5px;
  font-weight: 700;
  color: var(--paper);
  background: var(--ink);
  border-radius: var(--r-2);
  margin: 0 2px;
  vertical-align: super;
}
.specimen-receipt {
  display: flex;
  align-items: center;
  gap: 8px;
  border-top: 1px solid var(--ink);
  padding-top: 8px;
  font-size: var(--fs-12);
}
.sr-mark {
  width: 3px;
  height: 12px;
  background: var(--ink);
}
.sr-label {
  font-weight: 700;
  color: var(--ink);
}
.sr-id,
.sr-dim {
  color: var(--ink-3);
}
.sr-dim {
  color: var(--ink-2);
}
.sr-time {
  margin-left: auto;
  color: var(--ink-3);
}
.specimen-rows {
  border-top: 1px solid var(--rule-2);
  background: var(--paper-2);
  margin: 0 -18px;
  padding: 6px 18px 8px;
  border-radius: 0 0 var(--r-1) var(--r-1);
}
.specimen-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid var(--rule-2);
  font-size: var(--fs-12);
}
.specimen-row:last-of-type {
  border-bottom: none;
}
.sr-idx {
  font-weight: 700;
  color: var(--ink);
}
.sr-file {
  flex: 1;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sr-score {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--ink-2);
}
.specimen-meta {
  padding-top: 7px;
  font-size: var(--fs-11);
  color: var(--ink-3);
  line-height: 1.7;
}

/* ---- 手机：单列，回执示意放下方 ---- */
@media (max-width: 840px) {
  .auth-panel {
    grid-template-columns: 1fr;
    max-width: 460px;
  }
  .auth-specimen-col {
    border-left: none;
    border-top: 1px solid var(--rule);
    padding-top: 24px;
  }
  .auth-col {
    padding: 28px 24px 24px;
  }
}
</style>
