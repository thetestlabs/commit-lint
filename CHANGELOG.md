# CHANGELOG


## v0.2.0 (2025-03-28)

### Code Style

- Format using ruff and isort
  ([`1269941`](https://github.com/thetestlabs/commit-lint/commit/1269941258b4ded3cd28549cee53090426bbcdf3))

### Continuous Integration

- Troubleshooting workflow
  ([`2558243`](https://github.com/thetestlabs/commit-lint/commit/2558243c07dec98a400cc814d7c18e9d8f5fa75e))

- Troubleshooting workflow
  ([`f4981ba`](https://github.com/thetestlabs/commit-lint/commit/f4981ba4a497731d9020a824f5ef41cb106f5825))

- Troubleshooting workflow
  ([`efae625`](https://github.com/thetestlabs/commit-lint/commit/efae6257778fba6b4312cef4d674be40a0c40f8c))

- Update workflow file to use uv
  ([`3bc3c2c`](https://github.com/thetestlabs/commit-lint/commit/3bc3c2cfd247ca9a4937765446ba95c7c201aa8a))

### Documentation

- Add workflow badge to README
  ([`68af577`](https://github.com/thetestlabs/commit-lint/commit/68af5775464e4c93869ee08fea1ad0372e7a1596))

### Features

- Move project mananagement from poetry to uv
  ([`4cd9eb2`](https://github.com/thetestlabs/commit-lint/commit/4cd9eb2f0862748b1c2420a78f090fba749a12eb))

### Refactoring

- Remove redundant config files and update workflow
  ([`a8cc807`](https://github.com/thetestlabs/commit-lint/commit/a8cc8071fce80f05ba56b7915e6eeb56d6580611))


## v0.1.4 (2025-03-27)

### Bug Fixes

- Remove unused keyword
  ([`4d0adc5`](https://github.com/thetestlabs/commit-lint/commit/4d0adc54538cfb8e8d2983e8180a085c10b08c73))

### Refactoring

- Reduce cyclomatic complexity for three methods
  ([`62814e0`](https://github.com/thetestlabs/commit-lint/commit/62814e0bb4aa90716370119f2fa974e204206d36))


## v0.1.3 (2025-03-27)

### Bug Fixes

- Module imported multiple times
  ([`2cc8c8e`](https://github.com/thetestlabs/commit-lint/commit/2cc8c8e9298ef4c4c6b3938e28f157d05ac6d346))

- Module imported multiple times
  ([`8dc1552`](https://github.com/thetestlabs/commit-lint/commit/8dc1552a12fd783b0889dec886dec7e2d5ef4765))

- Resolve issue lists should be surrounded by blank lines
  ([`ff6e296`](https://github.com/thetestlabs/commit-lint/commit/ff6e29645bd02f848064800ba5cb0fdac0e556df))

### Refactoring

- Refactor create and init commands and add helper functions to reduce cyclomatic complexity
  ([`a54efdf`](https://github.com/thetestlabs/commit-lint/commit/a54efdfae715762122e25df50f3a667958dbc83a))

These refactorings significantly reduce the cyclomatic complexity by:

1. Extracting format-specific config generation into a dedicated helper 2. Separating file writing
  logic based on file type 3. Isolating validation and display logic 4. Breaking down large methods
  into smaller, focused functions with clear responsibilities

The code is now more maintainable, testable, and easier to understand.

### Testing

- Resolve issue with failing test when validating Jira style commit messages
  ([`92be997`](https://github.com/thetestlabs/commit-lint/commit/92be997a42a58d4e111895b0a3d9f7766f569117))


## v0.1.2 (2025-03-27)

### Bug Fixes

- Remove duplicate decorators
  ([`1a3a1c9`](https://github.com/thetestlabs/commit-lint/commit/1a3a1c9b052cfd0f55968fd68fdf079a3a502167))

- Removed unused imports
  ([`84af8a7`](https://github.com/thetestlabs/commit-lint/commit/84af8a7de79e0920cd4f257c2df014efc9bcd320))

- Resolve issue where breaking change info is not added to the footer
  ([`7f22b72`](https://github.com/thetestlabs/commit-lint/commit/7f22b726748faf2efc6ae7d092a5ff926450dc3d))

### Chores

- Fix rebase
  ([`89d0b8d`](https://github.com/thetestlabs/commit-lint/commit/89d0b8d0ec4eb5c6fc6d009610bb82e5b77656e3))

- Remove codacy config file
  ([`f1854e9`](https://github.com/thetestlabs/commit-lint/commit/f1854e90f0837593ad5855c936c90eea1896d964))

### Continuous Integration

- Add Codacity badge to README
  ([`3b37906`](https://github.com/thetestlabs/commit-lint/commit/3b37906d7d27a592636cbaff0ed494f0feabc0e8))

- Add Codacity config file to ignore assert statements used by pytest
  ([`ff989d2`](https://github.com/thetestlabs/commit-lint/commit/ff989d2531d6b220c10dbd016a9e1dd03f8e9fde))

- Add step to upload test coverage report to Codacy
  ([`19be44a`](https://github.com/thetestlabs/commit-lint/commit/19be44a2a75637b63ec3d156258d60268212b82d))

- Fix issue with uploading code coverage to Codacy
  ([`63efdb0`](https://github.com/thetestlabs/commit-lint/commit/63efdb07d796e64f0fd9e8afc4d27a7c4eba7c0a))

- Fix issue with uploading code coverage to Codacy
  ([`3a70c93`](https://github.com/thetestlabs/commit-lint/commit/3a70c93e6b6946934362cc237858af1af12350a9))

- Trigger build
  ([`8821a04`](https://github.com/thetestlabs/commit-lint/commit/8821a043bcc6928b918a36381ab816256c266af9))

- Trigger build
  ([`1c20624`](https://github.com/thetestlabs/commit-lint/commit/1c206247faa27fe229fb6b5fff4a24087bd2731a))

- Trigger build
  ([`9b482b4`](https://github.com/thetestlabs/commit-lint/commit/9b482b4a28a227878680b4cd646652a3939b20c3))

- Trigger build
  ([`c17f165`](https://github.com/thetestlabs/commit-lint/commit/c17f1650b6f999c563a71705bbb49361970a3dcd))

- Troubleshoot issues with missing dependencies
  ([`a3a8430`](https://github.com/thetestlabs/commit-lint/commit/a3a84308e1dfea7a70c344adb035463f9cb8de92))

- Troubleshoot issues with missing dependencies
  ([`83b3625`](https://github.com/thetestlabs/commit-lint/commit/83b3625005ff42347c3ec97af546ad4d2f0f44da))

- Troubleshoot issues with missing dependencies
  ([`7276925`](https://github.com/thetestlabs/commit-lint/commit/7276925656c3b73b8fc25b491229adb660a95c72))

- Troubleshoot issues with missing dependencies
  ([`f536ac7`](https://github.com/thetestlabs/commit-lint/commit/f536ac713a70f41a08a91b3d04cb9cae83716e3c))

- Troubleshoot issues with missing dependencies
  ([`87bbce7`](https://github.com/thetestlabs/commit-lint/commit/87bbce7e3d040d22765c3ad98d2709f2f12985be))

- Troubleshoot issues with missing dependencies
  ([`caaadf3`](https://github.com/thetestlabs/commit-lint/commit/caaadf3b6cc320419e64a143c3a8ece49310ba87))

- Troubleshoot issues with missing dependencies
  ([`20b121e`](https://github.com/thetestlabs/commit-lint/commit/20b121e594a8c8f2e2e2d53c3442c9b17b61ef8e))

- Update bandit configuration file to exclude the tests directory
  ([`a3e594d`](https://github.com/thetestlabs/commit-lint/commit/a3e594d6a7898c7bc3cbcfccce66bbcb64b98653))

### Refactoring

- Reduce cyclomatic complexity of methods by using helper functions
  ([`055257b`](https://github.com/thetestlabs/commit-lint/commit/055257b4f5ac97295f653c69b4c154e209a58d20))

- Remove duplicate code
  ([`bdb37a1`](https://github.com/thetestlabs/commit-lint/commit/bdb37a18d9725988c8bc8350eb2ff133d183dc21))

- Update code based on rules and format using ruff
  ([`1fcc057`](https://github.com/thetestlabs/commit-lint/commit/1fcc0577ba6271d724c3a3cec6f1f9e01b633dea))


## v0.1.1 (2025-03-26)

### Continuous Integration

- Explicitly install pytest and pytest-cov
  ([`0d01c0d`](https://github.com/thetestlabs/commit-lint/commit/0d01c0d43285d2900959fc611a5c2224993bd245))

- Remove separate workflow for publishing since it is now part of the release pipeline
  ([`2e8d64c`](https://github.com/thetestlabs/commit-lint/commit/2e8d64c3824152143d220a3d40aeb5863fde1cab))

- Troubleshoot issues with missing dependencies
  ([`8e0741d`](https://github.com/thetestlabs/commit-lint/commit/8e0741db4e7ea4d0271b564a4d25f65549ae7a2c))

- Troubleshoot issues with missing dependencies
  ([`890e1bc`](https://github.com/thetestlabs/commit-lint/commit/890e1bcb9ee192fc880d7c2ca7523674021d16f5))

- Troubleshoot issues with missing dependencies
  ([`3a08b9b`](https://github.com/thetestlabs/commit-lint/commit/3a08b9b8fa0d00cbdaf74419fa66cf18251f04ae))

- Troubleshoot issues with missing dependencies
  ([`0e8de84`](https://github.com/thetestlabs/commit-lint/commit/0e8de846a4d72daf48a3b3f728b8599e10f1e392))

- Troubleshoot issues with missing dependencies
  ([`af64362`](https://github.com/thetestlabs/commit-lint/commit/af643624bc5c66dbce3a6730310e0ea548f8abbd))

- Troubleshoot issues with missing dependencies
  ([`81ca59a`](https://github.com/thetestlabs/commit-lint/commit/81ca59ab35423254fbeb4c266e4a79311d048f7f))

- Troubleshoot issues with missing dependencies
  ([`f1f7c9d`](https://github.com/thetestlabs/commit-lint/commit/f1f7c9de2aefa4987a485ada52551dfbeaf34828))

- Update Poetry commands for workflow setup to include dev dependencies
  ([`49fa206`](https://github.com/thetestlabs/commit-lint/commit/49fa20661efe1e72eb83278686b271bc86851b81))

- Update workflow to include code coverage with pytest and codecov
  ([`a6858a4`](https://github.com/thetestlabs/commit-lint/commit/a6858a43f27e58352e6e37d28ac134d6dd8eae9a))

### Documentation

- Add docstrings to functions
  ([`dca6026`](https://github.com/thetestlabs/commit-lint/commit/dca60264abe2ec5fb19bfbf37148ef71dc7e4685))

### Refactoring

- Add option to use a standalone config file, commit-lint.toml, instead of pyproject.toml
  ([`0474b38`](https://github.com/thetestlabs/commit-lint/commit/0474b3820ca272e0db0901132eb7faafa60e887e))

### Testing

- Add additional test suites to bring code coverage up to 88%
  ([`41139ce`](https://github.com/thetestlabs/commit-lint/commit/41139ced1cfeeacf617de095c3b085c60fec3281))

- Add tests
  ([`327f5c8`](https://github.com/thetestlabs/commit-lint/commit/327f5c8f32b090f263100a972039b90e05e18f11))


## v0.1.0 (2025-03-25)

- Initial Release
