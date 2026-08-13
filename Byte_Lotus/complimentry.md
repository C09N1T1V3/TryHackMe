Complimentary
===============
Install the free app and it hands your phone a set of cloud keys, the same set it hands everyone. They're read-only, but read-only of every guest's contacts, location, and passwords, not just Lambo's. She gave consent. Technically.


AWS.config.credentials.get(function (err) {
  if (err) {
    console.error("Could not fetch guest credentials:", err);
    return;
  }

  const dynamodb = new AWS.DynamoDB({ region: "us-east-1" });
  dynamodb.scan(
    {
      TableName: "complimentary-GuestWellnessProfiles"
    },
    function (err, data) {
      if (err) {
        console.error("Could not load dashboard:", err);
        return;
      }
      console.log(data.Items);
    }
  );
});


