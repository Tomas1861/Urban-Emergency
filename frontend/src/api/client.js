import axios from "axios";
import { ElMessage } from "element-plus";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000",
  timeout: 90000,
});

// 后端统一响应体 {success, code, message, data, request_id}（第十一节）。
// 这里拆包成直接返回 data；失败时用 ElMessage 提示并抛出原始错误信息，
// 页面按需自行 catch 做更细粒度的处理（例如展示 agent_run_id / retryable）。
http.interceptors.response.use(
  (res) => {
    const body = res.data;
    if (body && typeof body === "object" && "success" in body) {
      if (!body.success) {
        const err = new Error(body.message || "请求失败");
        err.code = body.code;
        err.data = body.data;
        return Promise.reject(err);
      }
      return body.data;
    }
    return body;
  },
  (error) => {
    const detail = error.response?.data;
    const message =
      detail?.message || detail?.detail?.[0]?.msg || error.message || "网络错误";
    ElMessage.error(message);
    // 后端 BusinessError 即使返回非 2xx 状态码，body 仍是 {success:false, code, data} 结构，
    // 之前只在 2xx 分支解析过 code/data，导致所有 4xx/503 的业务错误码在页面里都读不到。
    if (detail && typeof detail === "object" && "success" in detail) {
      const err = new Error(detail.message || message);
      err.code = detail.code;
      err.data = detail.data;
      return Promise.reject(err);
    }
    return Promise.reject(error);
  }
);

export default http;
