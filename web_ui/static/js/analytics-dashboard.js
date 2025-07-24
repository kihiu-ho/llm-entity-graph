/**
 * Analytics Dashboard - Interactive dashboard with charts and metrics
 * Provides real-time analytics visualization for entity management
 */

class AnalyticsDashboard {
    constructor() {
        this.charts = new Map();
        this.refreshInterval = null;
        this.autoRefresh = false;
        this.refreshRate = 30000; // 30 seconds
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.setupAutoRefresh();
    }
    
    setupEventListeners() {
        // Chart control buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('chart-control')) {
                this.handleChartControl(e.target);
            }
            
            if (e.target.classList.contains('timeline-filter')) {
                this.handleTimelineFilter(e.target);
            }
            
            if (e.target.classList.contains('refresh-btn')) {
                this.refreshData();
            }
        });
        
        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('autoRefreshToggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                this.toggleAutoRefresh(e.target.checked);
            });
        }
    }
    
    async loadDashboardData() {
        try {
            this.showLoadingState();
            
            // Load overview data
            const overviewData = await this.fetchDashboardOverview();
            this.updateOverviewStats(overviewData);
            
            // Load charts data
            await this.loadCharts();
            
            // Load activity timeline
            await this.loadActivityTimeline();
            
            // Load recommendations
            await this.loadRecommendations();
            
            this.hideLoadingState();
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showErrorState('Failed to load dashboard data');
        }
    }
    
    async fetchDashboardOverview() {
        const response = await fetch('/api/analytics/dashboard');
        const data = await response.json();
        
        if (!data.success && data.error) {
            throw new Error(data.error);
        }
        
        return data;
    }
    
    updateOverviewStats(data) {
        // Update stat cards
        const stats = data.overview || {};
        
        this.updateStatCard('totalSessions', stats.total_sessions || 0);
        this.updateStatCard('totalEntities', stats.total_entities || 0);
        this.updateStatCard('totalRelationships', stats.total_relationships || 0);
        this.updateStatCard('approvalRate', `${stats.entity_approval_rate || 0}%`);
        
        // Update quality score
        const qualityScore = data.quality_metrics?.overall_score || 0;
        this.updateQualityScore(qualityScore);
        
        // Update quality metrics
        if (data.quality_metrics) {
            this.updateQualityMetrics(data.quality_metrics);
        }
    }
    
    updateStatCard(elementId, value, change = null) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            
            // Add animation
            element.classList.add('fade-in');
            setTimeout(() => element.classList.remove('fade-in'), 500);
        }
        
        // Update change indicator if provided
        if (change !== null) {
            const changeElement = document.getElementById(`${elementId.replace('total', '').replace('Rate', '')}Change`);
            if (changeElement) {
                changeElement.textContent = change > 0 ? `+${change}%` : `${change}%`;
                changeElement.className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
            }
        }
    }
    
    updateQualityScore(score) {
        const scoreElement = document.getElementById('overallQualityScore');
        if (scoreElement) {
            scoreElement.textContent = `${Math.round(score)}`;
            
            // Update color based on score
            scoreElement.className = 'quality-score';
            if (score >= 90) scoreElement.classList.add('excellent');
            else if (score >= 75) scoreElement.classList.add('good');
            else if (score >= 60) scoreElement.classList.add('fair');
            else scoreElement.classList.add('poor');
        }
    }
    
    updateQualityMetrics(metrics) {
        const metricElements = {
            'approvalScore': metrics.approval_score,
            'confidenceScore': metrics.confidence_score,
            'validationScore': metrics.validation_score,
            'completenessScore': 100 // Placeholder
        };
        
        Object.entries(metricElements).forEach(([elementId, value]) => {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = Math.round(value || 0);
            }
        });
    }
    
    async loadCharts() {
        try {
            // Load chart data
            const overviewData = await this.fetchDashboardOverview();
            
            // Create charts
            this.createStatusChart(overviewData.status_distribution);
            this.createTypeChart(overviewData.status_distribution);
            this.createConfidenceChart();
            this.createActivityChart();
            
        } catch (error) {
            console.error('Error loading charts:', error);
        }
    }
    
    createStatusChart(statusData) {
        const ctx = document.getElementById('statusChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.has('status')) {
            this.charts.get('status').destroy();
        }
        
        const entityData = statusData?.entities || {};
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(entityData).map(key => key.charAt(0).toUpperCase() + key.slice(1)),
                datasets: [{
                    data: Object.values(entityData),
                    backgroundColor: [
                        '#ffc107', // pending
                        '#28a745', // approved
                        '#dc3545', // rejected
                        '#17a2b8'  // edited
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        this.charts.set('status', chart);
    }
    
    createTypeChart(statusData) {
        const ctx = document.getElementById('typeChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.has('type')) {
            this.charts.get('type').destroy();
        }
        
        // Mock type distribution data
        const typeData = {
            'Person': 45,
            'Company': 30,
            'Organization': 15,
            'Location': 10
        };
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(typeData),
                datasets: [{
                    label: 'Count',
                    data: Object.values(typeData),
                    backgroundColor: [
                        '#007bff',
                        '#28a745',
                        '#ffc107',
                        '#dc3545'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        this.charts.set('type', chart);
    }
    
    createConfidenceChart() {
        const ctx = document.getElementById('confidenceChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.has('confidence')) {
            this.charts.get('confidence').destroy();
        }
        
        // Mock confidence distribution data
        const confidenceData = {
            'High (0.8-1.0)': 35,
            'Medium (0.5-0.8)': 45,
            'Low (0.0-0.5)': 20
        };
        
        const chart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: Object.keys(confidenceData),
                datasets: [{
                    data: Object.values(confidenceData),
                    backgroundColor: [
                        '#28a745',
                        '#ffc107',
                        '#dc3545'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        this.charts.set('confidence', chart);
    }
    
    createActivityChart() {
        const ctx = document.getElementById('activityChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.has('activity')) {
            this.charts.get('activity').destroy();
        }
        
        // Mock activity data for the last 7 days
        const labels = [];
        const entityData = [];
        const relationshipData = [];
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            entityData.push(Math.floor(Math.random() * 20) + 5);
            relationshipData.push(Math.floor(Math.random() * 15) + 3);
        }
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Entities',
                        data: entityData,
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Relationships',
                        data: relationshipData,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
        
        this.charts.set('activity', chart);
    }
    
    async loadActivityTimeline(days = 7) {
        try {
            const response = await fetch(`/api/analytics/activity-timeline?days=${days}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderActivityTimeline(data.timeline);
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error loading activity timeline:', error);
            this.showTimelineError();
        }
    }
    
    renderActivityTimeline(timeline) {
        const container = document.getElementById('timelineContent');
        if (!container) return;
        
        if (!timeline || timeline.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No recent activity</p>';
            return;
        }
        
        const timelineHTML = timeline.map(item => {
            const iconClass = this.getTimelineIconClass(item.type);
            const timeAgo = this.formatTimeAgo(item.timestamp);
            
            return `
                <div class="timeline-item">
                    <div class="timeline-icon ${iconClass}">
                        <i class="fas ${this.getTimelineIcon(item.type)}"></i>
                    </div>
                    <div class="timeline-content">
                        <div class="timeline-title-text">${this.getTimelineTitle(item)}</div>
                        <div class="timeline-description">${this.getTimelineDescription(item)}</div>
                        <div class="timeline-time">${timeAgo}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = timelineHTML;
    }
    
    getTimelineIconClass(type) {
        const iconClasses = {
            'session_created': 'session',
            'session_action': 'session',
            'entity_action': 'entity',
            'relationship_action': 'relationship',
            'approval': 'approval'
        };
        return iconClasses[type] || 'session';
    }
    
    getTimelineIcon(type) {
        const icons = {
            'session_created': 'fa-database',
            'session_action': 'fa-cog',
            'entity_action': 'fa-user',
            'relationship_action': 'fa-link',
            'approval': 'fa-check'
        };
        return icons[type] || 'fa-info';
    }
    
    getTimelineTitle(item) {
        switch (item.type) {
            case 'session_created':
                return 'New Session Created';
            case 'entity_action':
                return `Entity ${item.action}`;
            case 'relationship_action':
                return `Relationship ${item.action}`;
            default:
                return item.action || 'Activity';
        }
    }
    
    getTimelineDescription(item) {
        switch (item.type) {
            case 'session_created':
                return `${item.document_title} with ${item.details?.entities_count || 0} entities`;
            case 'entity_action':
                return `${item.entity_name} by ${item.user}`;
            case 'relationship_action':
                return `${item.relationship_type} by ${item.user}`;
            default:
                return item.description || '';
        }
    }
    
    async loadRecommendations() {
        try {
            const response = await fetch('/api/analytics/quality-report');
            const data = await response.json();
            
            if (data.success && data.recommendations) {
                this.renderRecommendations(data.recommendations);
            } else {
                throw new Error(data.error || 'No recommendations available');
            }
        } catch (error) {
            console.error('Error loading recommendations:', error);
            this.showRecommendationsError();
        }
    }
    
    renderRecommendations(recommendations) {
        const container = document.getElementById('recommendationsContent');
        if (!container) return;
        
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No recommendations at this time</p>';
            return;
        }
        
        const recommendationsHTML = recommendations.map(rec => `
            <div class="recommendation-item ${rec.priority}">
                <div class="recommendation-icon">
                    <i class="fas ${this.getRecommendationIcon(rec.priority)}"></i>
                </div>
                <div class="recommendation-content">
                    <div class="recommendation-title-text">${rec.title}</div>
                    <div class="recommendation-description">${rec.description}</div>
                    <div class="recommendation-action">${rec.action}</div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = recommendationsHTML;
    }
    
    getRecommendationIcon(priority) {
        const icons = {
            'high': 'fa-exclamation-triangle',
            'medium': 'fa-exclamation-circle',
            'low': 'fa-info-circle'
        };
        return icons[priority] || 'fa-info';
    }
    
    handleChartControl(button) {
        // Update active state
        const controls = button.parentElement.querySelectorAll('.chart-control');
        controls.forEach(ctrl => ctrl.classList.remove('active'));
        button.classList.add('active');
        
        // Update chart based on control
        const chartType = button.dataset.chart;
        const targetChart = button.dataset.target;
        const period = button.dataset.period;
        
        if (targetChart && chartType) {
            this.updateChart(targetChart, chartType);
        }
        
        if (targetChart && period) {
            this.updateActivityChart(period);
        }
    }
    
    handleTimelineFilter(button) {
        // Update active state
        const filters = button.parentElement.querySelectorAll('.timeline-filter');
        filters.forEach(filter => filter.classList.remove('active'));
        button.classList.add('active');
        
        // Load timeline with new filter
        const days = parseInt(button.dataset.days);
        this.loadActivityTimeline(days);
    }
    
    updateChart(chartId, dataType) {
        // This would update the chart with new data type
        // For now, just log the action
        console.log(`Updating ${chartId} with ${dataType} data`);
    }
    
    updateActivityChart(period) {
        // This would update the activity chart with new time period
        console.log(`Updating activity chart for ${period} days`);
    }
    
    setupAutoRefresh() {
        // Auto-refresh can be enabled/disabled
        this.toggleAutoRefresh(false);
    }
    
    toggleAutoRefresh(enabled) {
        this.autoRefresh = enabled;
        
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        if (enabled) {
            this.refreshInterval = setInterval(() => {
                this.refreshData();
            }, this.refreshRate);
        }
    }
    
    async refreshData() {
        try {
            await this.loadDashboardData();
            this.showRefreshSuccess();
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showRefreshError();
        }
    }
    
    showLoadingState() {
        // Show loading indicators
        const loadingElements = document.querySelectorAll('.loading-state');
        loadingElements.forEach(el => el.style.display = 'block');
    }
    
    hideLoadingState() {
        const loadingElements = document.querySelectorAll('.loading-state');
        loadingElements.forEach(el => el.style.display = 'none');
    }
    
    showErrorState(message) {
        console.error('Dashboard error:', message);
        // Could show error UI here
    }
    
    showTimelineError() {
        const container = document.getElementById('timelineContent');
        if (container) {
            container.innerHTML = '<div class="error-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load activity timeline</p></div>';
        }
    }
    
    showRecommendationsError() {
        const container = document.getElementById('recommendationsContent');
        if (container) {
            container.innerHTML = '<div class="error-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load recommendations</p></div>';
        }
    }
    
    showRefreshSuccess() {
        // Could show a brief success indicator
        console.log('Dashboard refreshed successfully');
    }
    
    showRefreshError() {
        // Could show a brief error indicator
        console.error('Failed to refresh dashboard');
    }
    
    formatTimeAgo(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.analyticsDashboard = new AnalyticsDashboard();
});

// Export for module use
window.AnalyticsDashboard = AnalyticsDashboard;
