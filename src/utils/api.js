const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiClient {
    constructor(baseUrl = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        // Get auth token from localStorage
        const token = localStorage.getItem('token');

        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` }),
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ message: response.statusText }));
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Templates
    async getTemplates() {
        return this.request('/templates');
    }

    async getTemplate(templateId) {
        return this.request(`/templates/${templateId}`);
    }

    // Services
    async createService(data) {
        return this.request('/services/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getServices(includeDeleted = false) {
        const query = includeDeleted ? '?include_deleted=true' : '';
        return this.request(`/services/${query}`);
    }

    async listServices(includeDeleted = false) {
        return this.getServices(includeDeleted);
    }

    async getService(serviceId) {
        return this.request(`/services/${serviceId}`);
    }

    async updateService(serviceId, data) {
        return this.request(`/services/${serviceId}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async stopService(serviceId) {
        return this.request(`/services/${serviceId}?status=inactive`, {
            method: 'PATCH',
        });
    }

    async startService(serviceId) {
        return this.request(`/services/${serviceId}?status=active`, {
            method: 'PATCH',
        });
    }

    async deleteService(serviceId) {
        return this.request(`/services/${serviceId}`, {
            method: 'DELETE',
        });
    }

    // WebSocket for logs
    createLogsWebSocket(serviceId, onMessage, onError, onClose) {
        const wsUrl = this.baseUrl.replace('http', 'ws').replace('/api', '');
        const ws = new WebSocket(`${wsUrl}/api/services/ws/${serviceId}/logs`);

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (onError) onError(error);
        };

        ws.onclose = () => {
            console.log('WebSocket closed');
            if (onClose) onClose();
        };

        return ws;
    }
}

export const apiClient = new ApiClient();
export default ApiClient;
