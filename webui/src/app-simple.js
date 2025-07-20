// MiniPAM Vue.js Application - Simple version without component recursion
const { createApp, ref, reactive, computed, onMounted, nextTick } = Vue;

// API Service
const apiService = {
  baseURL: '/api/v1',
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };
    
    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Network error' }));
        throw new Error(error.detail || error.message || `HTTP ${response.status}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },
  
  async getCidrs() {
    return await this.request('/cidrs');
  },
  
  async getCidr(cidr) {
    return await this.request(`/cidrs/${encodeURIComponent(cidr)}`);
  },
  
  async createCidr(data) {
    return await this.request('/cidrs', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  async updateCidr(cidr, data) {
    return await this.request(`/cidrs/${encodeURIComponent(cidr)}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  
  async deleteCidr(cidr) {
    return await this.request(`/cidrs/${encodeURIComponent(cidr)}`, {
      method: 'DELETE'
    });
  },
  
  async getCidrTree() {
    return await this.request('/cidrs/tree');
  },
  
  async getHealth() {
    return await this.request('/health/ready');
  }
};

// Main Application
const App = {
  data() {
    return {
      currentView: 'tree',
      loading: false,
      
      // Data
      cidrs: [],
      cidrTree: [],
      health: null,
      
      // UI State
      expandedNodes: {}, // Track which nodes are expanded
      
      // Search/Filter
      searchQuery: '',
      
      // Toast notifications
      toasts: [],
      toastId: 0
    };
  },
  
  computed: {
    // Flatten tree into a list with depth information
    flattenedTree() {
      const result = [];
      
      const flatten = (nodes, depth = 0) => {
        nodes.forEach(node => {
          result.push({
            ...node,
            depth,
            isExpanded: this.expandedNodes[node.cidr] !== false // Default to expanded for first 2 levels
          });
          
          if (node.children && node.children.length > 0 && this.expandedNodes[node.cidr] !== false) {
            flatten(node.children, depth + 1);
          }
        });
      };
      
      flatten(this.cidrTree);
      return result;
    }
  },
  
  async mounted() {
    await this.loadData();
    // Auto-expand first two levels
    this.flattenedTree.forEach(node => {
      if (node.depth < 2) {
        this.$set(this.expandedNodes, node.cidr, true);
      }
    });
  },
  
  methods: {
    // Data loading
    async loadData() {
      this.loading = true;
      try {
        const [cidrsResponse, tree, health] = await Promise.all([
          apiService.getCidrs(),
          apiService.getCidrTree(),
          apiService.getHealth()
        ]);
        
        this.cidrs = cidrsResponse.blocks || [];
        this.cidrTree = tree;
        this.health = health;
        
        console.log('Loaded tree:', this.cidrTree);
      } catch (error) {
        this.showToast('Failed to load data: ' + error.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    
    // Tree operations
    toggleNode(cidr) {
      this.$set(this.expandedNodes, cidr, !this.expandedNodes[cidr]);
    },
    
    hasChildren(node) {
      return node.children && node.children.length > 0;
    },
    
    // CRUD operations
    async createCidr(data) {
      try {
        await apiService.createCidr(data);
        this.showToast('CIDR created successfully', 'success');
        await this.loadData();
      } catch (error) {
        this.showToast('Failed to create CIDR: ' + error.message, 'error');
      }
    },
    
    async deleteCidr(cidr) {
      if (!confirm(`Are you sure you want to delete ${cidr}?`)) {
        return;
      }
      
      try {
        await apiService.deleteCidr(cidr);
        this.showToast('CIDR deleted successfully', 'success');
        await this.loadData();
      } catch (error) {
        this.showToast('Failed to delete CIDR: ' + error.message, 'error');
      }
    },
    
    // Toast notifications
    showToast(message, type = 'info') {
      const id = ++this.toastId;
      this.toasts.push({ id, message, type });
      setTimeout(() => {
        this.removeToast(id);
      }, 5000);
    },
    
    removeToast(id) {
      const index = this.toasts.findIndex(t => t.id === id);
      if (index > -1) {
        this.toasts.splice(index, 1);
      }
    }
  },
  
  template: `
    <div>
      <!-- Header -->
      <header class="header">
        <div class="container">
          <h1>MiniPAM</h1>
        </div>
      </header>
      
      <!-- Main Content -->
      <main class="main">
        <div class="container">
          <div class="card">
            <h2>CIDR Management</h2>
            
            <div v-if="loading">Loading...</div>
            
            <div v-else>
              <!-- Tree View -->
              <div class="tree">
                <div v-for="node in flattenedTree" :key="node.cidr">
                  <div 
                    class="tree-node" 
                    :style="{ paddingLeft: (node.depth * 2 + 1) + 'rem' }"
                  >
                    <span 
                      class="tree-toggle" 
                      @click="toggleNode(node.cidr)"
                      v-if="hasChildren(node)"
                    >
                      {{ node.isExpanded ? '▼' : '▶' }}
                    </span>
                    <span v-else style="display: inline-block; width: 1rem;"></span>
                    
                    <strong>{{ node.cidr }}</strong>
                    <span style="color: #666; margin-left: 0.5rem;">{{ node.name }}</span>
                    
                    <span style="margin-left: auto; display: flex; gap: 0.25rem;">
                      <button @click="deleteCidr(node.cidr)" class="btn btn-danger" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;">
                        Delete
                      </button>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
      
      <!-- Toast Notifications -->
      <div class="toast-container">
        <div 
          v-for="toast in toasts" 
          :key="toast.id"
          :class="['toast', toast.type]"
        >
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>{{ toast.message }}</span>
            <button @click="removeToast(toast.id)" class="modal-close" style="margin-left: 1rem;">&times;</button>
          </div>
        </div>
      </div>
    </div>
  `
};

// Create and mount the app
createApp(App).mount('#app');