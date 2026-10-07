<script setup>
/** 个人设置：查看账号信息 + 修改密码 */
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { changePassword } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ old_password: '', new_password: '', confirm: '' })

const rules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '新密码至少 8 位', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value && !/(?=.*[A-Za-z])(?=.*\d)/.test(value)) {
          callback(new Error('新密码必须同时包含字母和数字'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  confirm: [
    { required: true, message: '请再输入一次新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.new_password) {
          callback(new Error('两次输入的新密码不一致'))
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
    await changePassword({
      old_password: form.old_password,
      new_password: form.new_password,
    })
    ElMessage.success('密码修改成功')
    form.old_password = ''
    form.new_password = ''
    form.confirm = ''
    formRef.value.resetFields()
  } catch {
    /* 错误提示已由 request.js 统一弹出 */
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="profile-page">
    <div class="profile-card">
      <h3 class="card-title">账号信息</h3>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ userStore.username }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          {{ userStore.isAdmin ? '管理员（可管理知识库）' : '普通用户（问答）' }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="profile-card">
      <h3 class="card-title">修改密码</h3>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="90px"
        style="max-width: 460px"
      >
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="form.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="form.new_password"
            type="password"
            show-password
            placeholder="至少 8 位，含字母和数字"
          />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit">保存修改</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: flex-start;
}
.profile-card {
  width: 100%;
  max-width: 640px;
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px 24px;
}
.card-title {
  margin: 0 0 16px;
  font-size: 15px;
}
</style>
