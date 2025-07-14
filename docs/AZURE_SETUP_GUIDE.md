# Azure Entra ID Setup Guide for MiniPAM

This guide walks you through setting up Azure Entra ID (formerly Azure AD) authentication for MiniPAM.

## Prerequisites

- Azure subscription with Azure Active Directory
- Administrative access to Azure AD
- MiniPAM deployed and accessible

## Step 1: Register Application in Azure Portal

1. **Navigate to Azure Portal**
   - Go to [portal.azure.com](https://portal.azure.com)
   - Sign in with your Azure administrator account

2. **Open Azure Active Directory**
   - Search for "Azure Active Directory" in the top search bar
   - Click on the Azure Active Directory service

3. **Register New Application**
   - Navigate to **App registrations** in the left sidebar
   - Click **New registration**
   - Fill in the application details:
     - **Name**: `MiniPAM CIDR Management`
     - **Supported account types**: `Accounts in this organizational directory only (Single tenant)`
     - **Redirect URI**:
       - Type: `Web`
       - URL: `http://localhost:8000/auth/callback/oidc` (or your production URL)
   - Click **Register**

4. **Note Important Values**
   After registration, copy these values from the **Overview** page:
   - **Application (client) ID**: `12345678-1234-1234-1234-123456789abc`
   - **Directory (tenant) ID**: `87654321-4321-4321-4321-cba987654321`

## Step 2: Create Client Secret

1. **Navigate to Certificates & secrets**
   - In your app registration, click **Certificates & secrets** in the left sidebar
   - Click **New client secret**
   - Add description: `MiniPAM Authentication Secret`
   - Choose expiration: `24 months` (recommended)
   - Click **Add**

2. **Copy Secret Value**
   - **IMPORTANT**: Copy the secret **Value** immediately (not the Secret ID)
   - Store it securely - you won't be able to see it again
   - Example: `your~secret~value~here`

## Step 3: Configure API Permissions (Optional)

For enhanced functionality, add these permissions:

1. **Add Microsoft Graph Permissions**
   - Click **API permissions** in the left sidebar
   - Click **Add a permission** → **Microsoft Graph** → **Delegated permissions**
   - Add these permissions:
     - `User.Read` (usually already present)
     - `GroupMember.Read.All` (optional, for group membership)
   - Click **Add permissions**

2. **Grant Admin Consent**
   - Click **Grant admin consent for [Your Organization]**
   - Confirm by clicking **Yes**

## Step 4: Create Azure AD Security Groups

Create groups for role-based access control:

1. **Navigate to Groups**
   - Go back to Azure Active Directory main page
   - Click **Groups** in the left sidebar
   - Click **New group**

2. **Create Admin Group**
   - **Group type**: `Security`
   - **Group name**: `minipam-admins`
   - **Group description**: `MiniPAM administrators with read/write access`
   - **Membership type**: `Assigned`
   - Add initial members if desired
   - Click **Create**

3. **Create User Group**
   - Repeat the process for:
   - **Group name**: `minipam-users`
   - **Group description**: `MiniPAM users with read-only access`

## Step 5: Assign Users to Groups

1. **Open Group Management**
   - Navigate to **Azure Active Directory** → **Groups**
   - Click on `minipam-admins`

2. **Add Members**
   - Click **Members** in the left sidebar
   - Click **Add members**
   - Search for and select users who should have admin access
   - Click **Select**

3. **Repeat for User Group**
   - Do the same for `minipam-users` group

## Step 6: Configure MiniPAM

Update your MiniPAM configuration with the Azure values:

### Option A: Using Docker Compose Override

Create a `.env` file with your Azure values:

```bash
# Azure Entra ID Configuration
MINIPAM_AUTH_BACKEND=oidc
MINIPAM_JWT_SECRET=your-production-jwt-secret-here

# Azure Application Details (replace with your values)
MINIPAM_OIDC_CLIENT_ID=12345678-1234-1234-1234-123456789abc
MINIPAM_OIDC_CLIENT_SECRET=your~secret~value~here
MINIPAM_OIDC_ISSUER_URL=https://login.microsoftonline.com/87654321-4321-4321-4321-cba987654321/v2.0

# MiniPAM Configuration
MINIPAM_OIDC_REDIRECT_URI=http://localhost:8000/auth/callback/oidc
MINIPAM_OIDC_SCOPE=openid profile email
MINIPAM_OIDC_ROLE_CLAIM=groups
MINIPAM_OIDC_ROLE_MAPPING=minipam-admins:readwrite,minipam-users:readonly
MINIPAM_OIDC_DEFAULT_ROLE=readonly
```

Then start with:

```bash
docker-compose -f docker-compose.yml -f docker-compose.azure.yml up -d
```

### Option B: Direct Environment Variables

Modify your docker-compose.yml or set environment variables directly:

```yaml
environment:
  - MINIPAM_AUTH_BACKEND=oidc
  - MINIPAM_OIDC_CLIENT_ID=12345678-1234-1234-1234-123456789abc
  - MINIPAM_OIDC_CLIENT_SECRET=your~secret~value~here
  - MINIPAM_OIDC_ISSUER_URL=https://login.microsoftonline.com/87654321-4321-4321-4321-cba987654321/v2.0
  # ... other variables
```

## Step 7: Test the Configuration

1. **Start MiniPAM**

   ```bash
   docker-compose up -d
   ```

2. **Check Authentication Config**

   ```bash
   curl http://localhost:8000/auth/config
   ```

   Should return:

   ```json
   {
     "enabled": true,
     "backend": "oidc",
     "login_url": "https://login.microsoftonline.com/...",
     "supports_browser_flow": true
   }
   ```

3. **Test Login Flow**
   - Open browser and go to: `http://localhost:8000/auth/login/oidc`
   - You should be redirected to Microsoft login page
   - After login, you'll be redirected back to MiniPAM with a JWT token

4. **Verify User Info**

   ```bash
   # Use the token from step 3
   curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/auth/user
   ```

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Ensure the redirect URI in Azure matches exactly: `http://localhost:8000/auth/callback/oidc`
   - For production, use your actual domain with HTTPS

2. **"Invalid client secret"**
   - Verify you copied the secret **Value**, not the Secret ID
   - Check if the secret has expired

3. **"User not in any groups"**
   - Verify users are assigned to `minipam-admins` or `minipam-users` groups
   - Check the `MINIPAM_OIDC_ROLE_MAPPING` configuration

4. **"Permission denied"**
   - Ensure API permissions are granted and admin consent is provided
   - Check if `GroupMember.Read.All` permission is added if using group-based roles

### Debug Mode

Enable debug logging to troubleshoot:

```bash
MINIPAM_DEBUG=true
```

This will log detailed information about the OIDC authentication flow.

### Group ID vs Group Name

By default, Azure returns group Object IDs in the groups claim. If you need group names instead:

1. **Configure Group Claims in Azure**
   - Go to your app registration → **Token configuration**
   - Click **Add groups claim**
   - Select **Security groups** and **Group ID**

2. **Update Role Mapping**
   Use group Object IDs instead of names:

   ```bash
   MINIPAM_OIDC_ROLE_MAPPING=11111111-1111-1111-1111-111111111111:readwrite,22222222-2222-2222-2222-222222222222:readonly
   ```

## Production Considerations

1. **Use HTTPS**
   - Always use HTTPS in production
   - Update redirect URI to use your production domain

2. **Secure Secrets**
   - Use Azure Key Vault or similar for storing secrets
   - Use Docker secrets or Kubernetes secrets

3. **Certificate-based Authentication**
   - Consider using certificates instead of client secrets for enhanced security

4. **Monitoring**
   - Enable Azure AD sign-in logs for monitoring
   - Set up alerts for failed authentication attempts

## Security Best Practices

1. **Principle of Least Privilege**
   - Only assign necessary permissions
   - Use readonly role as default

2. **Regular Secret Rotation**
   - Rotate client secrets every 6-12 months
   - Update JWT secrets regularly

3. **Conditional Access**
   - Configure Azure AD Conditional Access policies
   - Require MFA for administrative access

4. **Audit Logging**
   - Enable authentication audit logs
   - Monitor group membership changes

## Support

For additional help:

- [Azure AD App Registration Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [OpenID Connect in Azure AD](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-protocols-oidc)
- MiniPAM Authentication Documentation
