/**
 * Job Trends Analyzer - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Show loader during ajax requests
    const loader = document.getElementById('loader-container');

    // Add event listeners to scrape and fetch buttons
    const scrapeButton = document.getElementById('scrape-button');
    if (scrapeButton) {
        scrapeButton.addEventListener('click', function() {
            scrapeJobs();
        });
    }

    const fetchButton = document.getElementById('fetch-button');
    if (fetchButton) {
        fetchButton.addEventListener('click', function() {
            fetchJobs();
        });
    }

    // Add event listener to search input
    const searchInput = document.getElementById('job-search');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            filterJobs();
        });
    }

    // Add event listeners to sort options
    const sortOptions = document.querySelectorAll('.sort-option');
    if (sortOptions) {
        sortOptions.forEach(option => {
            option.addEventListener('click', function() {
                const sortBy = this.getAttribute('data-sort');
                const sortOrder = this.getAttribute('data-order');
                sortJobs(sortBy, sortOrder);

                // Update button text
                const sortBtn = document.getElementById('sort-dropdown');
                if (sortBtn) {
                    sortBtn.innerText = `Sort: ${this.innerText}`;
                }
            });
        });
    }

    // Add event listeners to filter options
    const locationFilters = document.querySelectorAll('.location-filter');
    if (locationFilters) {
        locationFilters.forEach(filter => {
            filter.addEventListener('click', function() {
                const location = this.getAttribute('data-location');
                filterByLocation(location);

                // Update button text
                const locationBtn = document.getElementById('location-dropdown');
                if (locationBtn) {
                    locationBtn.innerText = `Location: ${location || 'All'}`;
                }
            });
        });
    }

    const companyFilters = document.querySelectorAll('.company-filter');
    if (companyFilters) {
        companyFilters.forEach(filter => {
            filter.addEventListener('click', function() {
                const company = this.getAttribute('data-company');
                filterByCompany(company);

                // Update button text
                const companyBtn = document.getElementById('company-dropdown');
                if (companyBtn) {
                    companyBtn.innerText = `Company: ${company || 'All'}`;
                }
            });
        });
    }

    // Function to scrape Internshala jobs
    function scrapeJobs() {
        showLoader();

        // Update UI to show we're working
        const statusArea = document.getElementById('status-message');
        if (statusArea) {
            statusArea.innerHTML = `
                <div class="alert alert-info" role="alert">
                    <i class="fas fa-spinner fa-spin"></i> Scraping Internshala jobs... This may take a minute.
                </div>
            `;
        }

        // Send AJAX request to scrape endpoint
        fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoader();

            if (data.success) {
                if (statusArea) {
                    statusArea.innerHTML = `
                        <div class="alert alert-success" role="alert">
                            <i class="fas fa-check-circle"></i> Successfully scraped ${data.count} jobs from Internshala!
                        </div>
                    `;
                }

                // Enable analyze button if both sources are fetched
                enableAnalyzeButton();
            } else {
                if (statusArea) {
                    statusArea.innerHTML = `
                        <div class="alert alert-danger" role="alert">
                            <i class="fas fa-exclamation-circle"></i> Failed to scrape jobs: ${data.error}
                        </div>
                    `;
                }
            }
        })
        .catch(error => {
            hideLoader();
            console.error('Error:', error);

            if (statusArea) {
                statusArea.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-circle"></i> An error occurred while scraping: ${error.message}
                    </div>
                `;
            }
        });
    }

    // Function to fetch Remotive jobs
    function fetchJobs() {
        showLoader();

        // Update UI to show we're working
        const statusArea = document.getElementById('status-message');
        if (statusArea) {
            statusArea.innerHTML = `
                <div class="alert alert-info" role="alert">
                    <i class="fas fa-spinner fa-spin"></i> Fetching jobs from Remotive API... Please wait.
                </div>
            `;
        }

        // Send AJAX request to fetch endpoint
        fetch('/fetch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoader();

            if (data.success) {
                if (statusArea) {
                    statusArea.innerHTML = `
                        <div class="alert alert-success" role="alert">
                            <i class="fas fa-check-circle"></i> Successfully fetched ${data.count} jobs from Remotive API!
                        </div>
                    `;
                }

                // Enable analyze button if both sources are fetched
                enableAnalyzeButton();
            } else {
                if (statusArea) {
                    statusArea.innerHTML = `
                        <div class="alert alert-danger" role="alert">
                            <i class="fas fa-exclamation-circle"></i> Failed to fetch jobs: ${data.error}
                        </div>
                    `;
                }
            }
        })
        .catch(error => {
            hideLoader();
            console.error('Error:', error);

            if (statusArea) {
                statusArea.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-circle"></i> An error occurred while fetching: ${error.message}
                    </div>
                `;
            }
        });
    }

    // Function to filter jobs based on search text
    function filterJobs() {
        const searchText = document.getElementById('job-search').value.toLowerCase();
        const jobCards = document.querySelectorAll('.job-card');

        jobCards.forEach(card => {
            const title = card.querySelector('.job-title').textContent.toLowerCase();
            const company = card.querySelector('.company-name').textContent.toLowerCase();
            const location = card.querySelector('.job-location').textContent.toLowerCase();
            const skills = card.querySelector('.job-skills').textContent.toLowerCase();

            if (title.includes(searchText) || 
                company.includes(searchText) || 
                location.includes(searchText) || 
                skills.includes(searchText)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });

        // Show message if no results
        const jobContainer = document.getElementById('job-listings');
        const noResults = document.getElementById('no-results');

        if (jobContainer) {
            let visibleCount = 0;
            jobCards.forEach(card => {
                if (card.style.display !== 'none') {
                    visibleCount++;
                }
            });

            if (visibleCount === 0 && noResults) {
                noResults.style.display = 'block';
            } else if (noResults) {
                noResults.style.display = 'none';
            }
        }
    }

    // Function to sort jobs
    function sortJobs(sortBy, sortOrder) {
        const jobContainer = document.getElementById('job-listings');
        const jobCards = Array.from(document.querySelectorAll('.job-card'));

        if (!jobContainer || !jobCards.length) return;

        jobCards.sort((a, b) => {
            let valueA, valueB;

            // Get values based on sort criteria
            if (sortBy === 'salary') {
                valueA = parseFloat(a.getAttribute('data-salary')) || 0;
                valueB = parseFloat(b.getAttribute('data-salary')) || 0;
            } else if (sortBy === 'location') {
                valueA = a.querySelector('.job-location').textContent.trim();
                valueB = b.querySelector('.job-location').textContent.trim();
            } else if (sortBy === 'company') {
                valueA = a.querySelector('.company-name').textContent.trim();
                valueB = b.querySelector('.company-name').textContent.trim();
            } else {
                valueA = a.querySelector('.job-title').textContent.trim();
                valueB = b.querySelector('.job-title').textContent.trim();
            }

            // Compare based on sort order
            if (sortOrder === 'asc') {
                if (sortBy === 'salary') {
                    return valueA - valueB;
                } else {
                    return valueA.localeCompare(valueB);
                }
            } else {
                if (sortBy === 'salary') {
                    return valueB - valueA;
                } else {
                    return valueB.localeCompare(valueA);
                }
            }
        });

        // Remove all existing cards
        while (jobContainer.firstChild) {
            jobContainer.removeChild(jobContainer.firstChild);
        }

        // Add sorted cards back
        jobCards.forEach(card => {
            jobContainer.appendChild(card);
        });
    }

    // Function to filter by location
    function filterByLocation(location) {
        const jobCards = document.querySelectorAll('.job-card');

        jobCards.forEach(card => {
            if (!location || location === 'All') {
                card.style.display = '';
            } else {
                const jobLocation = card.querySelector('.job-location').textContent.toLowerCase();
                if (jobLocation.includes(location.toLowerCase())) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            }
        });

        // Update no results message
        updateNoResultsMessage();
    }

    // Function to filter by company
    function filterByCompany(company) {
        const jobCards = document.querySelectorAll('.job-card');

        jobCards.forEach(card => {
            if (!company || company === 'All') {
                card.style.display = '';
            } else {
                const jobCompany = card.querySelector('.company-name').textContent.toLowerCase();
                if (jobCompany === company.toLowerCase()) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            }
        });

        // Update no results message
        updateNoResultsMessage();
    }

    // Helper function to update no results message
    function updateNoResultsMessage() {
        const jobContainer = document.getElementById('job-listings');
        const noResults = document.getElementById('no-results');

        if (jobContainer && noResults) {
            const jobCards = document.querySelectorAll('.job-card');
            let visibleCount = 0;

            jobCards.forEach(card => {
                if (card.style.display !== 'none') {
                    visibleCount++;
                }
            });

            if (visibleCount === 0) {
                noResults.style.display = 'block';
            } else {
                noResults.style.display = 'none';
            }
        }
    }

    // Function to enable analyze button
    function enableAnalyzeButton() {
        const analyzeBtn = document.getElementById('analyze-button');
        const predictBtn = document.getElementById('predict-button');
        const heatmapBtn = document.getElementById('heatmap-button');
        const wordcloudBtn = document.getElementById('wordcloud-button');

        if (analyzeBtn) analyzeBtn.classList.remove('disabled');
        if (predictBtn) predictBtn.classList.remove('disabled');
        if (heatmapBtn) heatmapBtn.classList.remove('disabled');
        if (wordcloudBtn) wordcloudBtn.classList.remove('disabled');
    }

    // Helper functions for loader
    function showLoader() {
        if (loader) {
            loader.style.display = 'flex';
        }
    }

    function hideLoader() {
        if (loader) {
            loader.style.display = 'none';
        }
    }
});