/**
 * Job Trends Analyzer - Charts JavaScript for Visualizations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the wordcloud page
    const wordcloudContainer = document.getElementById('skill-chart-container');
    if (wordcloudContainer && wordcloudData) {
        // Render skill frequency chart
        renderSkillFrequencyChart();
    }
    
    // Function to render skill frequency chart
    function renderSkillFrequencyChart() {
        // Get the top skills from the server-side data
        const topSkills = wordcloudData.top_skills || [];
        
        if (!topSkills || topSkills.length === 0) {
            // Show error message if no skills data
            const chartContainer = document.getElementById('skill-chart-container');
            if (chartContainer) {
                chartContainer.innerHTML = '<div class="alert alert-warning">No skills data available for chart.</div>';
            }
            return;
        }
        
        // Extract skill names and counts for the chart
        const skillNames = topSkills.map(item => item.skill);
        const skillCounts = topSkills.map(item => item.count);
        
        // Get the canvas element
        const ctx = document.getElementById('skill-chart').getContext('2d');
        
        // Create gradient background
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(67, 97, 238, 0.7)');
        gradient.addColorStop(1, 'rgba(58, 12, 163, 0.3)');
        
        // Create the chart
        const skillChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: skillNames,
                datasets: [{
                    label: 'Skill Frequency',
                    data: skillCounts,
                    backgroundColor: gradient,
                    borderColor: 'rgba(67, 97, 238, 1)',
                    borderWidth: 1,
                    borderRadius: 5,
                    barPercentage: 0.6,
                    categoryPercentage: 0.8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(67, 97, 238, 0.9)',
                        titleFont: {
                            family: 'Poppins',
                            size: 14
                        },
                        bodyFont: {
                            family: 'Poppins',
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                return `Frequency: ${context.raw}`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Top Skills in Job Market',
                        font: {
                            family: 'Poppins',
                            size: 18,
                            weight: 'bold'
                        },
                        padding: {
                            top: 10,
                            bottom: 30
                        },
                        color: '#2b2d42'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: {
                                family: 'Poppins',
                                size: 12
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                family: 'Poppins',
                                size: 12
                            },
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    // Render job source distribution pie chart on analysis page
    const sourceChartContainer = document.getElementById('source-chart-container');
    if (sourceChartContainer) {
        renderJobSourceChart();
    }
    
    // Function to render job source distribution chart
    function renderJobSourceChart() {
        // Count jobs by source
        const jobCards = document.querySelectorAll('.job-card');
        const sourceCounts = {
            'Internshala': 0,
            'Remotive': 0
        };
        
        jobCards.forEach(card => {
            const sourceBadge = card.querySelector('.source-badge');
            if (sourceBadge) {
                const source = sourceBadge.textContent.trim();
                if (sourceCounts.hasOwnProperty(source)) {
                    sourceCounts[source]++;
                }
            }
        });
        
        // Get the canvas element
        const ctx = document.getElementById('source-chart').getContext('2d');
        
        // Create the chart
        const sourceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(sourceCounts),
                datasets: [{
                    data: Object.values(sourceCounts),
                    backgroundColor: [
                        'rgba(67, 97, 238, 0.8)',
                        'rgba(76, 201, 240, 0.8)'
                    ],
                    borderColor: [
                        'rgba(67, 97, 238, 1)',
                        'rgba(76, 201, 240, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                family: 'Poppins',
                                size: 14
                            },
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(43, 45, 66, 0.9)',
                        titleFont: {
                            family: 'Poppins',
                            size: 14
                        },
                        bodyFont: {
                            family: 'Poppins',
                            size: 13
                        }
                    },
                    title: {
                        display: true,
                        text: 'Job Source Distribution',
                        font: {
                            family: 'Poppins',
                            size: 18,
                            weight: 'bold'
                        },
                        padding: {
                            top: 10,
                            bottom: 30
                        },
                        color: '#2b2d42'
                    }
                },
                cutout: '70%',
                animation: {
                    animateScale: true,
                    animateRotate: true
                }
            }
        });
    }
});
