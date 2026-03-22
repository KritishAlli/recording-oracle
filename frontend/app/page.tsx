async function getBackendStatus() {
  try {
    const res = await fetch("http://backend:8000/health")
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