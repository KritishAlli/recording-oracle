async function getBackendStatus() {
  try {
    const res = await fetch("http://127.0.0.1:8000/health")
    const data = await res.json()
    return data
  }
  catch {
    return {status: "unreachable"}
  }
}
export default async function Home() {
  const status = await getBackendStatus();
  return (
    <main>
    <h1>Meeting Oracle</h1>
    <p>Backend Status: {status.status}</p>
    </main>
  )
};