<script setup>
/**
 * 知识库管理页（仅管理员）
 * 功能：知识库的 查看 / 新建 / 编辑 / 删除 / 进入文档管理
 */
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createKb, deleteKb, listKbs, updateKb } from '@/api/admin'
import { formatTime } from '@/utils/format'

const router = useRouter()
const loading = ref(false)
const kbs = ref([])

const dialog = reactive({ visible: false, isEdit: false, kbId: null })
const formRef = ref()
const form = reactive({ name: '', description: '' })
const rules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { max: 50, message: '名称最多 50 个字', trigger: 'blur' },
  ],
}

async function load() {
  loading.value = true
  try {
    kbs.value = await listKbs()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialog.isEdit = false
  dialog.kbId = null
  form.name = ''
  form.description = ''
  dialog.visible = true
}

function openEdit(kb) {
  dialog.isEdit = true
  dialog.kbId = kb.id
  form.name = kb.name
  form.description = kb.description || ''
  dialog.visible = true
}

async function submitForm() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  if (dialog.isEdit) {
    await updateKb(dialog.kbId, { name: form.name, description: form.description })
    ElMessage.success('修改成功')
  } else {
    await createKb({ name: form.name, description: form.description })
    ElMessage.success('知识库创建成功，现在可以上传资料了')
  }
  dialog.visible = false
  load()
}

async function onDelete(kb) {
  try {
    await ElMessageBox.confirm(
      `确定删除知识库「${kb.name}」吗？\n其中 ${kb.document_count} 份文档和全部数据都会被清除，且不可恢复。`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  await deleteKb(kb.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="page-head">
      <div>
        <h2 class="page-title">知识库</h2>
        <p class="page-sub">商品资料的收录与索引</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建知识库</el-button>
    </div>

    <el-empty
      v-if="!loading && kbs.length === 0"
      description="还没有知识库，点右上角「新建知识库」开始"
    />

    <div class="kb-grid">
      <div v-for="kb in kbs" :key="kb.id" class="kb-card" @click="router.push(`/admin/kb/${kb.id}`)">
        <div class="kb-head">
          <span class="kb-name">{{ kb.name }}</span>
          <span class="kb-counts num">{{ kb.document_count }} 份 · {{ kb.chunk_count }} 段</span>
        </div>
        <div class="kb-desc">{{ kb.description || '（暂无描述）' }}</div>
        <div class="kb-foot">
          <span class="kb-time num">{{ formatTime(kb.created_at) }}</span>
          <span class="kb-actions" @click.stop>
            <button class="kb-op" type="button" @click="router.push(`/admin/kb/${kb.id}`)">
              管理资料
            </button>
            <button class="kb-op" type="button" @click="openEdit(kb)">编辑</button>
            <button class="kb-op danger" type="button" @click="onDelete(kb)">删除</button>
          </span>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="dialog.visible"
      :title="dialog.isEdit ? '编辑知识库' : '新建知识库'"
      width="460px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：电商商品知识库" maxlength="50" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="简单说明这个知识库存放什么资料（可留空）"
            maxlength="500"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">{{ dialog.isEdit ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--sp-4);
}
.kb-card {
  background: var(--panel);
  border: 1px solid var(--rule);
  border-radius: var(--r-1);
  padding: 16px 16px 10px;
  cursor: pointer;
  transition: border-color var(--dur-2) var(--ease);
}
.kb-card:hover {
  border-color: var(--ink-3);
}
.kb-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}
.kb-name {
  font-size: var(--fs-16);
  font-weight: 700;
}
.kb-counts {
  font-size: var(--fs-11);
  color: var(--ink-3);
  flex-shrink: 0;
}
.kb-desc {
  margin: 8px 0 12px;
  font-size: var(--fs-13);
  color: var(--ink-2);
  min-height: 20px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.kb-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--rule-2);
  padding: 6px 0;
}
.kb-time {
  font-size: var(--fs-11);
  color: var(--ink-3);
}
.kb-actions {
  display: flex;
  gap: 2px;
}
.kb-op {
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: var(--fs-12);
  color: var(--ink-3);
  padding: 3px 8px;
  border-radius: var(--r-2);
  cursor: pointer;
  transition: color var(--dur-1) var(--ease), background var(--dur-1) var(--ease);
}
.kb-op:hover {
  color: var(--ink);
  background: var(--tint);
}
.kb-op.danger:hover {
  color: var(--stamp);
}
</style>
