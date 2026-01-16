import axios from 'axios'

// Define fallback environment variables from define config in vite.config.ts
const env = import.meta.env

export const getEnv = async () => {
    // If running in electron, use IPC
    if (window.ipcRenderer) {
        return window.ipcRenderer.invoke('read-env')
    }

    // Otherwise, try to usage process.env pollyfilled by Vite
    return {
        API_URL: process.env.API_URL,
        API_TOKEN: process.env.API_TOKEN,
        OLLAMA_URL: process.env.OLLAMA_URL,
        OLLAMA_ENDPOINT: process.env.OLLAMA_ENDPOINT,
        MODEL_NAME: process.env.MODEL_NAME,
        SECOND_MODEL_NAME: process.env.SECOND_MODEL_NAME,
        THIRD_MODEL_NAME: process.env.THIRD_MODEL_NAME,
        LOW_QUALITY_TAG_ID: process.env.LOW_QUALITY_TAG_ID,
        HIGH_QUALITY_TAG_ID: process.env.HIGH_QUALITY_TAG_ID,
        MAX_DOCUMENTS: process.env.MAX_DOCUMENTS,
        NUM_LLM_MODELS: process.env.NUM_LLM_MODELS,
        IGNORE_ALREADY_TAGGED: process.env.IGNORE_ALREADY_TAGGED,
    }
}

export const apiRequest = async (config: any) => {
    if (window.ipcRenderer) {
        return window.ipcRenderer.invoke('api-request', config)
    }

    // Web Mode (Proxy)
    try {
        // Rewrite URLs to use proxy
        // If config.url contains config.API_URL, replace with /proxy/api
        // If config.url contains config.OLLAMA_URL, replace with /proxy/ollama

        let url = config.url
        const API_URL = process.env.API_URL || env.VITE_API_URL
        const OLLAMA_URL = process.env.OLLAMA_URL || env.VITE_OLLAMA_URL

        // Remove trailing slashes for comparison
        const cleanApiUrl = API_URL?.replace(/\/+$/, '')
        const cleanOllamaUrl = OLLAMA_URL?.replace(/\/+$/, '')

        if (cleanApiUrl && url.startsWith(cleanApiUrl)) {
            const originalUrl = url
            url = url.replace(cleanApiUrl, '/proxy/api')
            console.log(`[Proxy] Rewriting ${originalUrl} -> ${url}`)
        } else if (cleanOllamaUrl && url.startsWith(cleanOllamaUrl)) {
            const originalUrl = url
            url = url.replace(cleanOllamaUrl, '/proxy/ollama')
            console.log(`[Proxy] Rewriting ${originalUrl} -> ${url}`)
        }

        const response = await axios({
            ...config,
            url
        })

        return {
            data: response.data,
            status: response.status,
            headers: response.headers
        }
    } catch (error: any) {
        console.error('Web API Request Error:', error.message)
        return {
            error: true,
            message: error.message,
            response: error.response ? {
                data: error.response.data,
                status: error.response.status
            } : undefined
        }
    }
}
