FROM php:8.3-cli


# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    unzip \
    curl \
    libzip-dev \
    && docker-php-ext-install \
        pdo_mysql \
        zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer


# Application directory
WORKDIR /var/www/html


# Laravel development server
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8000"]