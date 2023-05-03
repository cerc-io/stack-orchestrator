const fs = require('fs');
const tomlJS = require('toml-js');
const toml = require('toml');
const { merge } = require('lodash')

const main = () => {
  const overrideConfigString = fs.readFileSync('environments/watcher-config.toml', 'utf-8');
  const configString = fs.readFileSync('environments/local.toml', 'utf-8');
  const overrideConfig = toml.parse(overrideConfigString)
  const config = toml.parse(configString)

  // Merge configs
  const updatedConfig = merge(config, overrideConfig);

  // Form dbConnectionString for jobQueue DB
  const parts = config.jobQueue.dbConnectionString.split("://");
  const credsAndDB = parts[1].split("@");
  const creds = credsAndDB[0].split(":");
  creds[0] = overrideConfig.database.username;
  creds[1] = overrideConfig.database.password;
  credsAndDB[0] = creds.join(":");
  const dbName = credsAndDB[1].split("/")[1]
  credsAndDB[1] = [overrideConfig.database.host, dbName].join("/");
  parts[1] = credsAndDB.join("@");

  updatedConfig.jobQueue.dbConnectionString = parts.join("://");

  updatedConfig.jobQueue.dbConnectionString = parts.join("://");

  fs.writeFileSync('environments/local.toml', tomlJS.dump(updatedConfig), 'utf-8');
}

main();
