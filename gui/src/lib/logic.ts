export const PROMPT_DEFINITION = `
Please review the following document content and determine if it is of low quality or high quality.
Low quality means the content contains many meaningless or unrelated words or sentences.
High quality means the content is clear, organized, and meaningful.
Step-by-step evaluation process:
1. Check for basic quality indicators such as grammar and coherence.
2. Assess the overall organization and meaningfulness of the content.
3. Make a final quality determination based on the above criteria.
Respond strictly with "low quality" or "high quality".
Content:
`

export async function evaluateContent(
    api: any,
    content: string,
    model: string,
    url: string,
    endpoint: string,
    docId: number
): Promise<string> {
    const maxLen = 4000
    const truncated = content.length > maxLen ? content.slice(0, maxLen) : content

    try {
        if (endpoint.includes('/v1/')) {
            const payload = {
                model: model,
                messages: [{ role: "user", content: `${PROMPT_DEFINITION}${truncated}` }],
                temperature: 0.0
            }
            const res = await api.apiRequest({
                method: 'post',
                url: `${url}${endpoint}`,
                data: payload,
                timeout: 120000 // 120s
            })

            if (res.error) throw new Error(res.message)

            const fullResponse = res.data?.choices?.[0]?.message?.content || ''
            if (fullResponse.toLowerCase().includes('high quality')) return 'high quality'
            if (fullResponse.toLowerCase().includes('low quality')) return 'low quality'
            return ''
        } else {
            const payload = { model: model, prompt: `${PROMPT_DEFINITION}${truncated}`, stream: false }
            const res = await api.apiRequest({
                method: 'post',
                url: `${url}${endpoint}`,
                data: payload,
                timeout: 120000
            })

            if (res.error) throw new Error(res.message)

            // Ollama might return multiple JSON lines if streaming, but we set stream: false (if supported) or handle it
            // The python code handled split("\n"), implying streaming or multiple objects.
            // If we assume non-streaming capability or handle text.
            // Let's assume standard JSON response for now, or text.
            // Python code handles newline split.

            let fullResponse = ''
            if (typeof res.data === 'string') {
                const lines = res.data.trim().split('\n')
                for (const line of lines) {
                    try {
                        const json = JSON.parse(line)
                        if (json.response) fullResponse += json.response
                    } catch (e) { }
                }
            } else if (res.data?.response) {
                fullResponse = res.data.response
            }

            if (fullResponse.toLowerCase().includes('high quality')) return 'high quality'
            if (fullResponse.toLowerCase().includes('low quality')) return 'low quality'
            return ''
        }
    } catch (error) {
        console.error(`Error evaluating doc ${docId} with model ${model}:`, error)
        return ''
    }
}

export async function generateTitle(
    api: any,
    content: string,
    model: string,
    url: string,
    endpoint: string
): Promise<string> {
    const maxLen = 1000
    const truncated = content.length > maxLen ? content.slice(0, maxLen) : content

    const prompt = `
    Du bist ein Experte für die Erstellung sinnvoller Dokumenttitel.
    Analysiere den folgenden Inhalt und erstelle einen prägnanten, aussagekräftigen Titel, 
    der den Inhalt treffend zusammenfasst.
    Der Titel sollte nicht länger als 100 Zeichen sein.
    Antworte nur mit dem Titel, ohne Erklärung oder zusätzlichen Text.
    
    Inhalt:
    ${truncated}
    `

    try {
        let title = ''
        if (endpoint.includes('/v1/')) {
            const payload = {
                model: model,
                messages: [{ role: "user", content: prompt }],
                temperature: 0.7
            }
            const res = await api.apiRequest({
                method: 'post',
                url: `${url}${endpoint}`,
                data: payload,
                timeout: 120000
            })
            if (res.error) throw new Error(res.message)
            title = res.data?.choices?.[0]?.message?.content || ''
        } else {
            const payload = { model: model, prompt: prompt, stream: false }
            const res = await api.apiRequest({
                method: 'post',
                url: `${url}${endpoint}`,
                data: payload,
                timeout: 120000
            })
            if (res.error) throw new Error(res.message)

            if (typeof res.data === 'string') {
                const lines = res.data.trim().split('\n')
                for (const line of lines) {
                    try {
                        const json = JSON.parse(line)
                        if (json.response) title += json.response
                    } catch (e) { }
                }
            } else if (res.data?.response) {
                title = res.data.response
            }
        }

        // Clean title
        title = title.replace(/\[THINK\].*?\[\/THINK\]/gs, '').trim()
        title = title.replace(/["']/g, '').trim()
        title = title.replace(/\n/g, ' ').trim()
        if (title.length > 100) title = title.substring(0, 97) + '...'

        return title
    } catch (error) {
        console.error('Error generating title:', error)
        return ''
    }
}
