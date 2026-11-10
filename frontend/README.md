# CareeriqAi

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 21.2.28.

## Development server

To start the development server with the Laravel API proxy, run from the frontend directory:

```bash
npm start
```

The npm start script loads proxy.conf.json and forwards /api/** requests to http://127.0.0.1:8000. Start the Laravel backend first. The authenticated browser E2E runner uses its own temporary proxy configuration.

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Vitest](https://vitest.dev/) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.

## Testing framework decision

The original CareerIQ-AI frontend development plan specifies
Jasmine and Karma. The Angular 21 frontend has been migrated
to Vitest with jsdom.

The migration removes Karma 6.4.4 and its deprecated
rimraf 3, glob 7, and inflight 1 dependency chain.

Angular currently considers Karma-to-Vitest migration
experimental.

Run unit tests using `npm test -- --watch=false`.
