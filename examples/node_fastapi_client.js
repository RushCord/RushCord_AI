// npm install axios form-data fs
const axios = require("axios");
const fs = require("fs");
const FormData = require("form-data");

const FASTAPI_BASE_URL =
  process.env.FASTAPI_BASE_URL || "http://localhost:8000/v1";
const SERVICE_API_KEY =
  process.env.SERVICE_API_KEY || "replace-with-your-internal-api-key";

const client = axios.create({
  baseURL: FASTAPI_BASE_URL,
  timeout: 20000,
  headers: {
    "X-API-Key": SERVICE_API_KEY,
  },
});

async function callChat() {
  const { data } = await client.post("/chat", {
    messages: [
      { role: "system", content: "Bạn là trợ lý hữu ích cho ứng dụng chat." },
      {
        role: "user",
        content: "Cho tôi 2 mẹo để chuẩn bị cho ngày demo backend.",
      },
    ],
  });

  console.log("chat:", data);
}

async function callSummarize() {
  const { data } = await client.post("/summarize", {
    messages: [
      {
        role: "user",
        content: "Chúng ta sẽ chia việc thành module xác thực và module chat.",
      },
      {
        role: "assistant",
        content: "Tốt. Hãy thêm mốc kiểm tra mỗi 3 ngày.",
      },
    ],
  });

  console.log("summary:", data);
}

async function callSpeechToText(audioPath) {
  const form = new FormData();
  form.append("file", fs.createReadStream(audioPath));

  const { data } = await client.post("/speech-to-text", form, {
    headers: {
      ...form.getHeaders(),
      "X-API-Key": SERVICE_API_KEY,
    },
    timeout: 45000,
  });

  console.log("speech-to-text:", data);
}

async function main() {
  await callChat();
  await callSummarize();

  // Uncomment when you have an audio file
  // await callSpeechToText("./sample.wav");
}

main().catch((err) => {
  if (err.response) {
    console.error("API error:", err.response.status, err.response.data);
    return;
  }
  console.error(err.message);
});
