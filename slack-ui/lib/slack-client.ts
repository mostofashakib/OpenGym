import { execFile } from "child_process"
import path from "path"

const BRIDGE_SCRIPT = path.join(process.cwd(), "scripts", "slack_bridge.py")

export function runSlackBridge(cmd: string, args: string[] = []): Promise<any> {
  return new Promise((resolve, reject) => {
    execFile(
      "python3",
      [BRIDGE_SCRIPT, cmd, ...args],
      {
        cwd: process.cwd(),
        env: {
          ...process.env,
          PYTHONPATH: `${path.join(process.cwd(), "environment")}:${process.env.PYTHONPATH || ""}`,
        },
        timeout: 10000,
      },
      (error, stdout, stderr) => {
        if (error) {
          try {
            const parsed = JSON.parse(stdout)
            return resolve(parsed)
          } catch {
            return reject(new Error(stderr || error.message))
          }
        }
        try {
          const parsed = JSON.parse(stdout)
          resolve(parsed)
        } catch (e) {
          resolve({ raw: stdout, stderr })
        }
      }
    )
  })
}

export async function listChannels() {
  return runSlackBridge("list_channels")
}

export async function getChannelMessages(channelId: string) {
  return runSlackBridge("get_messages", [channelId])
}

export async function getThreadReplies(threadTs: string, channelId: string) {
  return runSlackBridge("get_threads", [threadTs, channelId])
}

export async function listUsers() {
  return runSlackBridge("list_users")
}

export async function sendMessage(channelId: string, text: string) {
  return runSlackBridge("call_tool", [
    "send_message",
    JSON.stringify({ channel_id: channelId, text }),
  ])
}

export async function sendThreadReply(channelId: string, threadTs: string, text: string) {
  return runSlackBridge("call_tool", [
    "send_thread_reply",
    JSON.stringify({ channel_id: channelId, thread_ts: threadTs, text }),
  ])
}

export async function addReaction(channelId: string, ts: string, emoji: string) {
  return runSlackBridge("call_tool", [
    "add_reaction",
    JSON.stringify({ channel_id: channelId, ts, emoji }),
  ])
}

export async function exportState() {
  return runSlackBridge("export_state")
}
